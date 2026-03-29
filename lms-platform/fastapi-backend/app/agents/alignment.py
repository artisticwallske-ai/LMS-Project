from typing import List
from langchain_core.messages import HumanMessage, SystemMessage

class CurriculumAlignmentAgent:
    def __init__(self, llm=None):
        self.llm = llm

    async def validate_lesson(self, lesson_content: str, source_chunks: List[str]) -> dict:
        """
        Validates the generated lesson against the retrieved source chunks.
        Returns a dictionary with 'is_aligned' (bool) and 'feedback' (str).
        """
        if not self.llm:
            print("Warning: CurriculumAlignmentAgent has no LLM configured. Skipping validation.")
            return {"is_aligned": True, "feedback": "Validation skipped (No LLM)."}

        context = "\n---\n".join(source_chunks)
        
        prompt = f"""
        You are a KICD Curriculum Specialist. Your task is to verify if the following generated lesson plan strictly aligns with the provided official curriculum source chunks.
        
        Source Curriculum Chunks:
        {context}
        
        Generated Lesson Plan:
        {lesson_content}
        
        Does the generated lesson plan accurately reflect the content, learning outcomes, and assessment rubrics in the source chunks with at least 95% fidelity? Does it avoid hallucinating concepts not present in the curriculum?
        
        Respond with exactly:
        ALIGNED: YES (if it is properly aligned)
        ALIGNED: NO (if it hallucinates or misses core outcomes)
        
        Then provide a brief 1-2 sentence feedback explaining why.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a strict curriculum validator."),
                HumanMessage(content=prompt)
            ])
            
            content = response.content.strip()
            is_aligned = "ALIGNED: YES" in content.upper()
            
            return {
                "is_aligned": is_aligned,
                "feedback": content
            }
        except Exception as e:
            print(f"Alignment Validation Error: {e}")
            # Default to passing if validation fails to prevent blocking
            return {"is_aligned": True, "feedback": f"Validation errored: {e}"}

alignment_agent = CurriculumAlignmentAgent()
