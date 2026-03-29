from .base import BaseAgent

class MathematicsAgent(BaseAgent):
    def __init__(self):
        super().__init__("Mathematics")

    @property
    def system_role(self) -> str:
        return "You focus on logical flow, step-by-step problem solving, and clear visual explanations. Emphasize numeracy and computational thinking."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Mental math or review activity"
        }

class EnglishAgent(BaseAgent):
    def __init__(self):
        super().__init__("English")

    @property
    def system_role(self) -> str:
        return "You focus on language acquisition, grammar, vocabulary, and reading comprehension. Encourage communication and collaboration."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Song, story, or picture discussion"
        }

class KiswahiliAgent(BaseAgent):
    def __init__(self):
        super().__init__("Kiswahili")

    @property
    def system_role(self) -> str:
        return "You are an expert in Kiswahili. Output the lesson plan primarily in English but include key Kiswahili terms and phrases where appropriate for the lesson content (Sarufi, Msamiati, Ufahamu)."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Wimbo au hadithi (Song or story)"
        }

class ScienceTechnologyAgent(BaseAgent):
    def __init__(self):
        super().__init__("Science & Technology")

    @property
    def system_role(self) -> str:
        return "You focus on inquiry-based learning, experiments, and observation. SAFETY IS PARAMOUNT. You must always include safety precautions for experiments."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Phenomenon observation or question"
        }

class AgricultureAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agriculture")

    @property
    def system_role(self) -> str:
        return "You focus on practical farming skills, soil conservation, and animal husbandry. Emphasize hygiene and tool safety."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Discuss importance of the activity"
        }

class HomeScienceAgent(BaseAgent):
    def __init__(self):
        super().__init__("Home Science")

    @property
    def system_role(self) -> str:
        return "You focus on nutrition, hygiene, cooking, and household management. Emphasize cleanliness and safety in the home environment."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Hygiene or nutrition review"
        }

class CreativeArtsAgent(BaseAgent):
    def __init__(self):
        super().__init__("Creative Arts")

    @property
    def system_role(self) -> str:
        return "You focus on expression, creativity, and technique in Art, Craft, and Music."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Appreciation of existing work"
        }

class PHEAgent(BaseAgent):
    def __init__(self):
        super().__init__("Physical & Health Education")

    @property
    def system_role(self) -> str:
        return "You focus on physical fitness, rules of games, sportsmanship, and health. Safety during play is key."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Specific physical exercises to prepare"
        }

class SocialStudiesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Social Studies")

    @property
    def system_role(self) -> str:
        return "You focus on history, geography, citizenship, and culture. Encourage critical thinking about society."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Map work or historical question"
        }

class ReligiousEducationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Religious Education")

    @property
    def system_role(self) -> str:
        return "You focus on moral values, spiritual growth, and understanding religious texts (Bible/Quran/Hindu Scriptures)."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Song or verse"
        }

class IndigenousLanguagesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Indigenous Languages")

    @property
    def system_role(self) -> str:
        return "You focus on the preservation and usage of local languages, culture, and oral traditions."

    @property
    def output_format_instructions(self) -> dict:
        return {
            "warmup": "Proverb, riddle, or song"
        }
