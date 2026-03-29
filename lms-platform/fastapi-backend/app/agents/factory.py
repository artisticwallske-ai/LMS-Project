from typing import Optional
from .base import BaseAgent
from .subjects import (
    MathematicsAgent, 
    EnglishAgent, 
    KiswahiliAgent, 
    ScienceTechnologyAgent, 
    AgricultureAgent, 
    HomeScienceAgent, 
    CreativeArtsAgent, 
    PHEAgent, 
    SocialStudiesAgent, 
    ReligiousEducationAgent, 
    IndigenousLanguagesAgent
)

class AgentFactory:
    SUPPORTED_SUBJECTS = [
        "Mathematics",
        "English",
        "Kiswahili",
        "Science & Technology",
        "Agriculture",
        "Home Science",
        "Creative Arts",
        "Physical & Health Education",
        "Social Studies",
        "Religious Education",
        "Indigenous Languages"
    ]

    def __init__(self):
        self._agents = {}

    def get_supported_subjects(self) -> list[str]:
        return self.SUPPORTED_SUBJECTS

    def get_agent(self, subject_name: str) -> BaseAgent:
        """
        Returns the appropriate agent instance for the given subject.
        Uses a flyweight/singleton pattern to reuse agent instances.
        """
        # Normalize subject name (simple lowercase check)
        key = subject_name.lower().strip()
        
        if key in self._agents:
            return self._agents[key]

        agent = self._create_agent(key)
        self._agents[key] = agent
        return agent

    def _create_agent(self, key: str) -> BaseAgent:
        if "math" in key:
            return MathematicsAgent()
        elif "english" in key:
            return EnglishAgent()
        elif "kiswahili" in key:
            return KiswahiliAgent()
        elif "science" in key or "sci" in key:
            return ScienceTechnologyAgent()
        elif "agri" in key:
            return AgricultureAgent()
        elif "home" in key:
            return HomeScienceAgent()
        elif "art" in key or "creative" in key:
            return CreativeArtsAgent()
        elif "pe" in key or "physical" in key:
            return PHEAgent()
        elif "social" in key:
            return SocialStudiesAgent()
        elif "religio" in key or "cre" in key or "ire" in key or "hre" in key:
            return ReligiousEducationAgent()
        elif "language" in key or "indigenous" in key:
            return IndigenousLanguagesAgent()
        else:
            # Fallback for unknown subjects, default to a generic Science/Tech behavior or Basic
            # For now, let's use SocialStudies as a generic "Text-heavy" fallback or create a GenericAgent
            # But simpler to just default to English structure for text or Science for practicals.
            # Let's map to EnglishAgent as a safe default for text-based learning
            print(f"Warning: No specific agent for '{key}'. Defaulting to EnglishAgent.")
            return EnglishAgent()

agent_factory = AgentFactory()
