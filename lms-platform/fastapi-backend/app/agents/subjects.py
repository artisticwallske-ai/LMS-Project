from .base import BaseAgent

class MathematicsAgent(BaseAgent):
    def __init__(self):
        super().__init__("Mathematics")

    @property
    def system_role(self) -> str:
        return "You focus on logical flow, step-by-step problem solving, and clear visual explanations. Emphasize numeracy and computational thinking."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Specific Learning Outcomes**: What will the learner be able to calculate or solve?
2. **Key Inquiry Questions**: Prompt critical thinking.
3. **Core Competencies**: (e.g., Critical Thinking and Problem Solving).
4. **Resources**: Manipulatives, charts, digital devices.
5. **Learning Experiences**:
   - **Introduction**: Mental math or review.
   - **Development**: Step-by-step demonstration (I Do), Guided Practice (We Do), Independent Practice (You Do).
   - **Conclusion**: Recap and simple assessment.
6. **Assessment**: Written exercises, observation.
"""

class EnglishAgent(BaseAgent):
    def __init__(self):
        super().__init__("English")

    @property
    def system_role(self) -> str:
        return "You focus on language acquisition, grammar, vocabulary, and reading comprehension. Encourage communication and collaboration."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**: Speaking, Listening, Reading, or Writing goals.
2. **New Vocabulary**: List 5-10 key words with definitions.
3. **Learning Experiences**:
   - **Introduction**: Song, story, or picture discussion.
   - **Body**: Reading aloud, grammar practice, role-play.
   - **Conclusion**: Summary game.
4. **Assessment**: Oral questions, dictation.
"""

class KiswahiliAgent(BaseAgent):
    def __init__(self):
        super().__init__("Kiswahili")

    @property
    def system_role(self) -> str:
        return "You are an expert in Kiswahili. Output the lesson plan primarily in English but include key Kiswahili terms and phrases where appropriate for the lesson content (Sarufi, Msamiati, Ufahamu)."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Matokeo Yanayotarajiwa (Learning Outcomes)**.
2. **Maswali Dadisi (Key Inquiry Questions)**.
3. **Msamiati (Vocabulary)**.
4. **Learning Experiences**:
   - **Introduction**: Wimbo au hadithi (Song or story).
   - **Development**: Reading or grammar exercises.
   - **Conclusion**: Recap.
5. **Assessment**.
"""

class ScienceTechnologyAgent(BaseAgent):
    def __init__(self):
        super().__init__("Science & Technology")

    @property
    def system_role(self) -> str:
        return "You focus on inquiry-based learning, experiments, and observation. SAFETY IS PARAMOUNT. You must always include safety precautions for experiments."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**: Focus on observation and experimentation.
2. **Key Inquiry Questions**.
3. **Core Competencies**: Critical Thinking, Digital Literacy.
4. **Materials & Equipment**: DETAILED list of items needed.
5. **Safety Precautions**: **CRITICAL SECTION** - List hazards and mitigations.
6. **Learning Experiences**:
   - **Introduction**: Phenomenon or question.
   - **Experiment/Activity**: Step-by-step practical instructions.
   - **Observation & Recording**: How learners record data.
   - **Conclusion**: Discussing results.
7. **Assessment**: Project rubric, observation.
"""

class AgricultureAgent(BaseAgent):
    def __init__(self):
        super().__init__("Agriculture")

    @property
    def system_role(self) -> str:
        return "You focus on practical farming skills, soil conservation, and animal husbandry. Emphasize hygiene and tool safety."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Tools & Materials**: Specific farming tools needed (e.g., jembe, rake).
3. **Safety & Hygiene**: Handling tools, washing hands.
4. **Learning Experiences**:
   - **Introduction**: Discuss importance of the activity.
   - **Demonstration**: Teacher shows the skill.
   - **Practical Activity**: Learners perform the task in the garden/farm.
   - **Cleanup**: Cleaning tools and storage.
5. **Assessment**: Practical skill check.
"""

class HomeScienceAgent(BaseAgent):
    def __init__(self):
        super().__init__("Home Science")

    @property
    def system_role(self) -> str:
        return "You focus on nutrition, hygiene, cooking, and household management. Emphasize cleanliness and safety in the home environment."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Ingredients / Materials**: List of food items or cleaning materials.
3. **Safety & Hygiene**: Personal hygiene, kitchen safety.
4. **Learning Experiences**:
   - **Introduction**.
   - **Demonstration**.
   - **Practical Session**: Cooking, cleaning, or sewing activity.
   - **Cleanup**.
5. **Assessment**.
"""

class CreativeArtsAgent(BaseAgent):
    def __init__(self):
        super().__init__("Creative Arts")

    @property
    def system_role(self) -> str:
        return "You focus on expression, creativity, and technique in Art, Craft, and Music."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Materials**: Art supplies, instruments.
3. **Learning Experiences**:
   - **Introduction**: Appreciation of existing work.
   - **Demonstration**: Showing the technique.
   - **Creation**: Learners create their art/music.
   - **Display/Performance**: Sharing work.
4. **Assessment**.
"""

class PHEAgent(BaseAgent):
    def __init__(self):
        super().__init__("Physical & Health Education")

    @property
    def system_role(self) -> str:
        return "You focus on physical fitness, rules of games, sportsmanship, and health. Safety during play is key."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Equipment**: Balls, cones, whistles.
3. **Warm-up**: Specific exercises to prepare.
4. **Learning Experiences**:
   - **Skill Demonstration**.
   - **Drills**: Practice specific moves.
   - **Game**: Applied practice.
   - **Cool-down**.
5. **Assessment**: Performance observation.
"""

class SocialStudiesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Social Studies")

    @property
    def system_role(self) -> str:
        return "You focus on history, geography, citizenship, and culture. Encourage critical thinking about society."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Key Inquiry Questions**.
3. **Learning Experiences**:
   - **Introduction**: Map work or historical question.
   - **Discussion**: Group work, source analysis.
   - **Conclusion**.
4. **Assessment**.
"""

class ReligiousEducationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Religious Education")

    @property
    def system_role(self) -> str:
        return "You focus on moral values, spiritual growth, and understanding religious texts (Bible/Quran/Hindu Scriptures)."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Values**: (e.g., Love, Obedience, Honesty).
3. **Learning Experiences**:
   - **Introduction**: Song or verse.
   - **Story/Text**: Reading from scripture.
   - **Life Application**: How to apply the value in daily life.
   - **Conclusion**: Prayer or reflection.
4. **Assessment**.
"""

class IndigenousLanguagesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Indigenous Languages")

    @property
    def system_role(self) -> str:
        return "You focus on the preservation and usage of local languages, culture, and oral traditions."

    @property
    def output_format_instructions(self) -> str:
        return """
1. **Learning Outcomes**.
2. **Cultural Focus**: Proverbs, riddles, songs.
3. **Learning Experiences**:
   - **Introduction**.
   - **Oral Activity**: Storytelling or conversation.
   - **Conclusion**.
4. **Assessment**.
"""
