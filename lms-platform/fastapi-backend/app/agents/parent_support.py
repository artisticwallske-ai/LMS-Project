from langchain_core.messages import HumanMessage, SystemMessage

class ParentSupportAgent:
    def __init__(self, llm=None):
        self.llm = llm

    async def generate_tip(self, topic: str = "General", grade: str = "Grade 4") -> str:
        if not self.llm:
            return f"Encourage your child to read for 15 minutes today! (Topic: {topic})"
            
        system_prompt = "You are an expert CBC parent coach. Provide one short, practical, 2-sentence tip for a parent homeschooling their child."
        user_prompt = f"The child is in {grade} and currently studying {topic}. Give a creative, screen-free activity the parent can do to reinforce this."
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return response.content.strip()
        except Exception as e:
            print(f"ParentSupportAgent Error: {e}")
            return "Have a 5-minute conversation with your child about what they learned today."

parent_support_agent = ParentSupportAgent()
