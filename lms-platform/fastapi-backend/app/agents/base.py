from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.knowledge_graph_neo4j import neo4j_service as knowledge_graph_service

class BaseAgent(ABC):
    """
    Abstract Base Class for all Subject Agents.
    """
    
    def __init__(self, subject_name: str):
        self.subject_name = subject_name
    
    @property
    @abstractmethod
    def system_role(self) -> str:
        """Define the specific role/persona of the agent."""
        pass

    @property
    def output_format_instructions(self) -> dict:
        """Define specific instructions for the template sections if needed."""
        return {}
    
    async def generate_lesson(self, topic: str, grade: str, vectorstore, llm, is_practical: bool = False) -> dict:
        """
        Orchestrates the lesson generation process:
        1. Fetch Context (RAG)
        2. Fetch Prerequisites (KG)
        3. Generate Prompt
        4. Call LLM
        """
        
        # 1. Retrieve relevant documents (RAG)
        context = ""
        sources = []
        if vectorstore:
            try:
                # Add subject to search query for better precision
                search_query = f"{self.subject_name} {topic}"
                print(f"[{self.subject_name} Agent] Searching for: {search_query}")
                docs = vectorstore.similarity_search(search_query, k=3)
                if docs:
                    context = "\n\n".join([d.page_content for d in docs])
                    sources = list(set([d.metadata.get("source", "Unknown") for d in docs]))
            except Exception as e:
                print(f"Retrieval error: {e}")
                context = "Curriculum data unavailable."

        # 2. Fetch Prerequisites (Knowledge Graph)
        prereqs = knowledge_graph_service.get_prerequisites(topic)
        prereq_text = ""
        if prereqs:
            prereq_list = [p['source_topic'] for p in prereqs]
            prereq_text = f"\n**Prerequisites found in Knowledge Graph:** {', '.join(prereq_list)}"
        
        # 3. Construct Prompts
        system_prompt = f"""You are an expert {self.subject_name} educator for the Kenyan Competency Based Curriculum (CBC).
{self.system_role}

Create a detailed 40-minute lesson plan for {grade} on the topic: "{topic}".
Use the provided curriculum content context to ensure strict alignment.

{prereq_text}

You MUST strictly follow this exact Markdown structure for the lesson:
**Header**: {grade} | {self.subject_name} | Theme | Strand | Sub-strand | CBC Learning Outcome Code(s)
**Core Competency Focus**: [Explicitly list which of the 7 CBC competencies are developed]
**Values Integration**: [Responsibility, Respect, etc.]
**PCIs (Pertinent & Contemporary Issues)**: [Any relevant PCIs addressed]
**Key Inquiry Question**: [Anchor learning question]

**WARM-UP (5 min)**: {self.output_format_instructions.get('warmup', 'Vocabulary activation or review') if isinstance(self.output_format_instructions, dict) else 'Vocabulary activation or review'}
**CONCEPT INTRODUCTION (10 min)**: [New knowledge delivery grounded in retrieved curriculum chunk]
**GUIDED PRACTICE (12 min)**: [Collaborative activity from Suggested Learning Experiences]
**INDEPENDENT ACTIVITY (8 min)**: [Learner performs task; include hints]
**ASSESSMENT CHECK (3 min)**: [2–3 targeted oral/written questions mapped to SLO]
**REFLECTION & CLOSURE (2 min)**: [Learner self-assesses; formative feedback using CBC rubric language]

**Resources**: [Suggested digital/physical materials]
**RAG Citations**: [List source documents/chunks used]

Keep the tone professional, instructional, and engaging for {grade} learners.
"""

        user_prompt = f"""
        Context from Curriculum Design:
        {context}
        
        Topic: {topic}
        Grade: {grade}
        Practical Session: {"Yes" if is_practical else "No"}
        """
        
        # 4. Generate Content
        content = ""
        if llm:
            max_retries = 2
            attempt = 0
            is_aligned = False
            feedback_prompt = ""
            
            while attempt < max_retries and not is_aligned:
                try:
                    print(f"[{self.subject_name} Agent] Invoking LLM (Attempt {attempt+1})...")
                    
                    # Add feedback if it's a retry
                    current_user_prompt = user_prompt
                    if feedback_prompt:
                        current_user_prompt += f"\n\nFeedback from previous attempt:\n{feedback_prompt}\nPlease revise the lesson plan to address this."
                        
                    response = await llm.ainvoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=current_user_prompt)
                    ])
                    content = response.content
                    
                    # 5. Validate Alignment
                    from app.agents.alignment import alignment_agent
                    source_chunks = [d.page_content for d in docs] if vectorstore and docs else [context]
                    validation_result = await alignment_agent.validate_lesson(content, source_chunks)
                    
                    if validation_result["is_aligned"]:
                        print(f"[{self.subject_name} Agent] Lesson successfully aligned.")
                        is_aligned = True
                    else:
                        print(f"[{self.subject_name} Agent] Lesson alignment failed. Feedback: {validation_result['feedback']}")
                        feedback_prompt = validation_result['feedback']
                        attempt += 1
                        
                except Exception as e:
                    print(f"LLM Generation Error: {e}")
                    content = f"Error generating lesson with LLM: {str(e)}\n\nUsing fallback content."
                    break
                    
            if not is_aligned and not content.startswith("Error"):
                print(f"[{self.subject_name} Agent] Warning: Max retries reached. Returning partially aligned lesson.")
                content = f"**[Alignment Warning: This lesson may not perfectly align with official curriculum]**\n\n{content}"
        else:
            content = self._generate_mock_content(topic, grade, context)

        return {
            "title": f"{self.subject_name} Lesson: {topic}",
            "content": content,
            "sources": sources
        }

    def _generate_mock_content(self, topic: str, grade: str, context: str) -> str:
        """Fallback for when LLM is not available."""
        return f"""
# {self.subject_name} Lesson Plan: {topic} (MOCK)
**Grade:** {grade}

> **Note:** Real AI generation is disabled. Configure LLM_API_KEY.

## 1. Learning Outcomes
By the end of the lesson, the learner should be able to...

## 2. Learning Experiences
1.  **Introduction**: ...
2.  **Activity**: ...

## 3. Assessment
*   Observation

**Context:**
{context[:200]}...
"""
