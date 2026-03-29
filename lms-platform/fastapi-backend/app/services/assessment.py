from uuid import UUID
import uuid
import json
from typing import List, Optional
from datetime import datetime
import asyncio
from app.core.database import supabase_client
from app.schemas import SBARecordCreate, SBARecordOut, KNECScore, MockExamRequest, MockExamResponse, Question, QuestionType
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.notification import notification_service

class AssessmentService:
    def __init__(self):
        self.client = supabase_client

    def record_sba_result(self, record: SBARecordCreate) -> SBARecordOut:
        data = {
            "learner_id": str(record.learner_id),
            "learning_outcome_id": str(record.learning_outcome_id),
            "score": record.score.value,
            "comments": record.comments,
            "recorded_at": datetime.now().isoformat(),
            "parent_acknowledged": False,
            "grade_level": record.grade_level,
            "academic_year": record.academic_year,
            "term": record.term
        }
        
        response = self.client.table("sba_records").insert(data).execute()
        created_record = response.data[0]
        
        # Update Knowledge Tracing Model
        mastery_prob = None
        try:
            mastery_prob = self.update_mastery_probability(str(record.learner_id), str(record.learning_outcome_id), record.score.value)
        except Exception as e:
            print(f"BKT Update Failed: {e}")

        # Fetch outcome details for display
        outcome_res = self.client.table("learning_outcomes").select("description, code").eq("id", str(record.learning_outcome_id)).execute()
        if outcome_res.data:
            outcome = outcome_res.data[0]
            created_record["outcome_description"] = outcome.get("description")
            created_record["outcome_code"] = outcome.get("code")
        
        # Check for intervention trigger
        try:
            outcome_desc = created_record.get("outcome_description") or "Unknown Outcome"
            notification_service.check_intervention_trigger(
                learner_id=record.learner_id,
                learning_outcome_id=record.learning_outcome_id,
                current_score=record.score.value,
                outcome_description=outcome_desc,
                mastery_probability=mastery_prob
            )
        except Exception as e:
            print(f"Intervention Check Failed: {e}")
            
        return created_record

    def get_learner_sba_history(self, learner_id: UUID) -> List[SBARecordOut]:
        response = self.client.table("sba_records")\
            .select("*, learning_outcomes(description, code)")\
            .eq("learner_id", str(learner_id))\
            .order("recorded_at", desc=True)\
            .execute()
            
        records = []
        for r in response.data:
            # Flatten outcome details
            outcome = r.get("learning_outcomes")
            if outcome:
                r["outcome_description"] = outcome.get("description")
                r["outcome_code"] = outcome.get("code")
            records.append(r)
            
        return records

    def get_longitudinal_analytics(self, learner_id: UUID):
        # Fetch raw scores
        response = self.client.table("sba_records")\
            .select("score, grade_level, academic_year, term, recorded_at")\
            .eq("learner_id", str(learner_id))\
            .order("academic_year")\
            .order("term")\
            .execute()
            
        score_map = {
            "EE1": 4, "EE2": 3.5, 
            "ME1": 3, "ME2": 2.5, 
            "AE1": 2, "AE2": 1.5, 
            "BE1": 1, "BE2": 0.5
        }
        
        # Aggregate by Grade+Term
        grouped = {}
        for r in response.data:
            key = f"{r['grade_level']} Term {r['term']}"
            if key not in grouped:
                grouped[key] = {"sum": 0, "count": 0, "year": r['academic_year'], "term": r['term'], "grade": r['grade_level']}
            
            val = score_map.get(r['score'], 0)
            grouped[key]["sum"] += val
            grouped[key]["count"] += 1
            
        result = []
        for key, val in grouped.items():
            result.append({
                "period": key,
                "average_score": round(val["sum"] / val["count"], 2),
                "grade": val["grade"],
                "term": val["term"]
            })
            
        return result

    def acknowledge_sba(self, record_id: UUID) -> bool:
        response = self.client.table("sba_records").update({"parent_acknowledged": True}).eq("id", str(record_id)).execute()
        return len(response.data) > 0

    def _calculate_bkt_update(self, current_prob: float, is_correct: bool) -> float:
        # Standard BKT Parameters
        p_transit = 0.1
        p_guess = 0.2
        p_slip = 0.1
        
        if is_correct:
            numerator = current_prob * (1 - p_slip)
            denominator = numerator + (1 - current_prob) * p_guess
        else:
            numerator = current_prob * p_slip
            denominator = numerator + (1 - current_prob) * (1 - p_guess)
            
        posterior = numerator / denominator if denominator > 0 else 0
        new_prob = posterior + (1 - posterior) * p_transit
        return min(max(new_prob, 0.0), 1.0) # Clamp between 0 and 1

    def update_mastery_probability(self, learner_id: str, outcome_id: str, score_val: str) -> float:
        # 1. Determine correctness (EE1-ME2 = Correct, AE1-BE2 = Incorrect)
        is_correct = score_val in ["EE1", "EE2", "ME1", "ME2"]
        
        # 2. Fetch current mastery
        res = self.client.table("competency_mastery")\
            .select("mastery_probability")\
            .eq("learner_id", learner_id)\
            .eq("learning_outcome_id", outcome_id)\
            .execute()
            
        current_prob = 0.3 # Default prior for new skill
        if res.data:
            current_prob = res.data[0]["mastery_probability"]
            
        # 3. Calculate new probability
        new_prob = self._calculate_bkt_update(current_prob, is_correct)
        
        # 4. Upsert
        data = {
            "learner_id": learner_id,
            "learning_outcome_id": outcome_id,
            "mastery_probability": new_prob,
            "last_updated": datetime.now().isoformat()
        }
        
        # Using on_conflict logic requires constraints, ensuring unique(learner_id, learning_outcome_id)
        self.client.table("competency_mastery").upsert(data, on_conflict="learner_id, learning_outcome_id").execute()
        
        return new_prob

    async def generate_mock_exam(self, request: MockExamRequest, vectorstore, llm) -> MockExamResponse:
        # 1. Determine Subjects
        subjects = request.subjects
        if not subjects:
            # Default to core subjects if none specified
            if request.grade_level in ["Grade 7", "Grade 8", "Grade 9"]:
                subjects = ["English", "Kiswahili", "Mathematics", "Integrated Science", "Social Studies"]
            else:
                subjects = ["English", "Mathematics", "Science"]

        all_questions = []
        
        async def generate_subject_questions(subject):
            questions = []
            # 2a. Retrieve context
            query = f"{request.grade_level} {subject} key concepts assessment"
            docs = []
            try:
                # Note: similarity_search is synchronous in LangChain FAISS by default, 
                # but we are in an async function. If vectorstore supports async, use it.
                # If not, it blocks the event loop briefly. For parallelization, we might need run_in_executor
                # if it's slow, but for k=2 it's usually fast.
                if vectorstore:
                    docs = vectorstore.similarity_search(query, k=2)
            except Exception as e:
                print(f"Vector search failed for {subject}: {e}")
            
            context = "\n".join([d.page_content for d in docs]) if docs else "No specific curriculum context available."

            # 2b. Generate Questions via LLM
            if llm:
                prompt = f"""
                Create 3 multiple-choice questions for a {request.grade_level} {subject} mock exam (KJSEA style).
                Based on:
                {context[:1000]}
                
                Return ONLY a JSON array of objects with fields: 'text', 'options' (array of 4 strings), 'correct_answer' (string matching one option).
                Do not include any markdown formatting or explanation. Just the raw JSON.
                """
                
                try:
                    response = await llm.ainvoke([
                        SystemMessage(content="You are an assessment expert. Output valid JSON only."),
                        HumanMessage(content=prompt)
                    ])
                    content = response.content
                    # Cleanup markdown code blocks if present
                    # Robust extraction of JSON content
                    import re
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
                    if json_match:
                        content = json_match.group(1)
                    
                    questions_data = json.loads(content)
                    
                    for q_data in questions_data:
                        questions.append(Question(
                            id=str(uuid.uuid4()),
                            text=q_data["text"],
                            type=QuestionType.MCQ,
                            options=q_data["options"],
                            correct_answer=q_data["correct_answer"],
                            subject=subject
                        ))
                except Exception as e:
                    print(f"Error generating questions for {subject}: {e}")
                    # Fallback Mock Question
                    questions.append(Question(
                        id=str(uuid.uuid4()),
                        text=f"Sample Question for {subject} (LLM Error)",
                        type=QuestionType.MCQ,
                        options=["Option A", "Option B", "Option C", "Option D"],
                        correct_answer="Option A",
                        subject=subject
                    ))
            else:
                # Fallback if no LLM
                 questions.append(Question(
                    id=str(uuid.uuid4()),
                    text=f"Sample Question for {subject} (No LLM)",
                    type=QuestionType.MCQ,
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_answer="Option A",
                    subject=subject
                ))
            return questions

        # 2. Parallel Execution
        results = await asyncio.gather(*[generate_subject_questions(sub) for sub in subjects])
        for res in results:
            all_questions.extend(res)

        return MockExamResponse(
            title=f"KJSEA Mock Exam - {request.grade_level}",
            grade_level=request.grade_level,
            questions=all_questions
        )

assessment_service = AssessmentService()
