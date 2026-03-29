from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class TutorAgent:
    def __init__(self, llm=None):
        self.llm = llm
        # Simple memory store for demo purposes. In prod, use Redis per learner session.
        self.memory = {} 

    async def get_response(self, session_id: str, user_text: str, context: str = "") -> str:
        if not self.llm:
            return "I'm sorry, my AI brain is currently offline. Please configure the LLM_API_KEY."

        if session_id not in self.memory:
            self.memory[session_id] = []
            
        history = self.memory[session_id]

        system_prompt = f"""You are an encouraging and patient CBC (Competency Based Curriculum) Teacher for a primary school student in Kenya. 
Your goal is to guide the student using Socratic dialogue. Do not just give them the answer. 
Ask probing questions, encourage them to think, and praise their efforts.

Curriculum Context for this session:
{context if context else 'General conversation'}

Rules:
1. Keep your responses short (1-3 sentences).
2. Ask one question at a time.
3. Be very encouraging.
"""

        messages = [SystemMessage(content=system_prompt)]
        
        # Append history
        for msg in history[-6:]: # Keep last 6 turns
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
                
        messages.append(HumanMessage(content=user_text))

        try:
            response = await self.llm.ainvoke(messages)
            ai_text = response.content
            
            # Update memory
            history.append({"role": "user", "content": user_text})
            history.append({"role": "assistant", "content": ai_text})
            
            return ai_text
        except Exception as e:
            print(f"TutorAgent Error: {e}")
            return "I'm having trouble thinking right now. Could you repeat that?"

tutor_agent = TutorAgent()
