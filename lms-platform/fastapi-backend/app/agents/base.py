from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.knowledge_graph import knowledge_graph_service

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
    @abstractmethod
    def output_format_instructions(self) -> str:
        """Define the specific output structure required."""
        pass
    
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

Create a detailed 35-minute lesson plan for {grade} on the topic: "{topic}".
Use the provided curriculum content context to ensure alignment.

{prereq_text}

Format the output in clear Markdown with the following sections:
{self.output_format_instructions}

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
            try:
                print(f"[{self.subject_name} Agent] Invoking LLM...")
                response = await llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])
                content = response.content
            except Exception as e:
                print(f"LLM Generation Error: {e}")
                content = f"Error generating lesson with LLM: {str(e)}\n\nUsing fallback content."
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
