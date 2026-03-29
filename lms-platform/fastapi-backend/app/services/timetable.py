from datetime import date, timedelta, time
from uuid import UUID
from typing import List, Optional
from app.core.database import supabase_client
from app.schemas import TimetableCreate, TimetableOut, TimetableEntryCreate, ActivityType

class TimetableService:
    def __init__(self):
        self.client = supabase_client

    def _get_or_create_subject(self, name: str, grade: str) -> Optional[str]:
        """Helper to fetch or create subjects."""
        # Check if exists
        try:
            response = self.client.table("subjects").select("id").eq("name", name).eq("grade_level", grade).execute()
            if response.data:
                return response.data[0]["id"]
            
            # Create
            response = self.client.table("subjects").insert({"name": name, "grade_level": grade}).execute()
            if response.data:
                return response.data[0]["id"]
        except Exception as e:
            print(f"Error creating subject {name}: {e}")
        return None

    def get_subjects_map(self, grade: str) -> dict:
        """Fetch all subjects for a grade and return name->id map."""
        try:
            response = self.client.table("subjects").select("id, name").eq("grade_level", grade).execute()
            return {s["name"]: s["id"] for s in response.data}
        except Exception as e:
            print(f"Error fetching subjects map: {e}")
            return {}

    def generate_timetable(self, learner_id: UUID, start_date: date, term: int, grade_level: Optional[str] = None) -> TimetableOut:
        # 1. Fetch Learner Grade (or use override)
        grade = grade_level or "Grade 4" # Default
        if not grade_level:
            try:
                learner_res = self.client.table("profiles").select("grade_level").eq("id", str(learner_id)).execute()
                if learner_res.data and learner_res.data[0].get("grade_level"):
                    grade = learner_res.data[0]["grade_level"]
            except Exception as e:
                print(f"Error fetching learner grade: {e}")

        # 2. Create the parent Timetable record
        timetable_data = {
            "learner_id": str(learner_id),
            "week_start_date": start_date.isoformat(),
            "term": term
        }
        
        try:
            # Check if already exists to avoid duplicates for the same week
            existing = self.client.table("timetables").select("*").eq("learner_id", str(learner_id)).eq("week_start_date", start_date.isoformat()).execute()
            if existing.data:
                timetable_id = existing.data[0]["id"]
                # Clear existing entries to regenerate
                self.client.table("timetable_entries").delete().eq("timetable_id", timetable_id).execute()
            else:
                response = self.client.table("timetables").insert(timetable_data).execute()
                timetable_id = response.data[0]["id"]
        except Exception as e:
            print(f"Error creating/fetching timetable record: {e}")
            raise e

        # 3. Define Subjects & Rules based on Grade
        # Optimize: Fetch all existing subjects first
        existing_subjects = self.get_subjects_map(grade)
        
        def get_sub_id(name):
            if name in existing_subjects:
                return existing_subjects[name]
            return self._get_or_create_subject(name, grade)

        is_jss = grade in ["Grade 7", "Grade 8", "Grade 9"]
        
        if is_jss:
            # Junior Secondary (9 Subjects)
            subjects = {
                "eng": get_sub_id("English"),
                "kis": get_sub_id("Kiswahili"),
                "math": get_sub_id("Mathematics"),
                "sci": get_sub_id("Integrated Science"),
                "pre_tech": get_sub_id("Pre-Technical Studies"),
                "ss": get_sub_id("Social Studies"),
                "biz": get_sub_id("Business Studies"),
                "arts": get_sub_id("Creative Arts"),
                "phe": get_sub_id("Physical & Health Ed")
            }
            
            # JSS Matrix (5 slots per day for MVP, 9 subjects rotated)
            schedule_matrix = {
                1: ["math", "eng", "kis", "sci", "pre_tech"],
                2: ["math", "eng", "ss", "biz", "arts"],
                3: ["math", "eng", "kis", "sci", "phe"],
                4: ["math", "eng", "ss", "pre_tech", "arts"],
                5: ["math", "eng", "kis", "sci", "biz"]
            }
        else:
            # Upper Primary (Grade 4-6) - Default
            subjects = {
                "math": get_sub_id("Mathematics"),
                "eng": get_sub_id("English"),
                "kis": get_sub_id("Kiswahili"),
                "sci": get_sub_id("Integrated Science"),
                "ss": get_sub_id("Social Studies"),
                "cre": get_sub_id("Religious Education"),
                "arts": get_sub_id("Creative Arts"),
                "agri": get_sub_id("Agriculture"),
                "pe": get_sub_id("Physical Education")
            }
            
            schedule_matrix = {
                1: ["math", "eng", "kis", "sci", "agri"],
                2: ["math", "eng", "ss", "cre", "arts"],
                3: ["math", "eng", "kis", "sci", "pe"],
                4: ["math", "eng", "ss", "agri", "arts"],
                5: ["math", "eng", "kis", "sci", "cre"]
            }
        
        # 4. Generate Entries (Mon-Fri)
        entries = []
        
        slots = [
            {"start": time(8, 0), "end": time(8, 40)},
            {"start": time(8, 50), "end": time(9, 30)},
            # Break 9:30-10:00
            {"start": time(10, 0), "end": time(10, 40)},
            {"start": time(10, 50), "end": time(11, 30)},
            # Lunch 11:30-12:30
            {"start": time(12, 30), "end": time(13, 10)},
        ]

        for day in range(1, 6): # 1=Mon, 5=Fri
            daily_subjects = schedule_matrix.get(day, [])
            skip_next = False
            
            for i, subject_key in enumerate(daily_subjects):
                if skip_next:
                    skip_next = False
                    continue
                    
                if i >= len(slots): break # Safety check
                
                slot = slots[i]
                subject_id = subjects.get(subject_key)
                
                if not subject_id:
                    continue

                activity_type = ActivityType.LESSON
                end_time = slot["end"]
                
                # Check for Double Block Practicals (minimum 80 minutes)
                if subject_key in ["sci", "agri", "arts", "pre_tech"] and i == 3:
                     activity_type = ActivityType.PRACTICAL
                     end_time = time(12, 10) # 10:50 to 12:10 (80 mins)
                     skip_next = True # Skip slot 4 (index 4)
                elif subject_key in ["sci", "agri", "arts", "pe"] and i == 4:
                     activity_type = ActivityType.PRACTICAL

                entry = {
                    "timetable_id": timetable_id,
                    "day_of_week": day,
                    "start_time": slot["start"].strftime("%H:%M:%S"),
                    "end_time": end_time.strftime("%H:%M:%S"),
                    "subject_id": subject_id,
                    "activity_type": activity_type.value,
                    "notes": f"{subject_key.upper()} {'Practical' if activity_type == ActivityType.PRACTICAL else 'Lesson'}"
                }
                entries.append(entry)

        # Bulk insert
        if entries:
            try:
                self.client.table("timetable_entries").insert(entries).execute()
            except Exception as e:
                print(f"Error inserting timetable entries: {e}")
                # We might want to raise here or return partial success
                # For now, we log and proceed to return what we can
        
        # 5. Return populated timetable
        return self.get_timetable(timetable_id)

    def get_timetable(self, timetable_id: str) -> Optional[TimetableOut]:
        # Fetch parent
        try:
            t_res = self.client.table("timetables").select("*").eq("id", timetable_id).execute()
            if not t_res.data:
                return None
            timetable = t_res.data[0]
            
            # Fetch entries
            e_res = self.client.table("timetable_entries").select("*, subjects(name)").eq("timetable_id", timetable_id).execute()
            
            entries = []
            for e in e_res.data:
                # Flatten subject name if available
                subj_name = e["subjects"]["name"] if e.get("subjects") else None
                e["subject_name"] = subj_name
                entries.append(e)
                
            timetable["entries"] = entries
            return timetable
        except Exception as e:
            print(f"Error fetching timetable: {e}")
            return None

timetable_service = TimetableService()
