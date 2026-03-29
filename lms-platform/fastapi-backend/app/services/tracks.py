from typing import List, Dict, Optional
from uuid import UUID
from app.schemas import Track
from app.core.database import supabase_client

# Hardcoded subject mappings for MVP
# In a real system, these might be in a database table 'track_subjects'
TRACK_SUBJECTS = {
    Track.STEM: {
        "core": ["English", "Kiswahili", "Mathematics", "Community Service Learning"],
        "electives": ["Physics", "Chemistry", "Biology", "Computer Science"]
    },
    Track.SOCIAL_SCIENCES: {
        "core": ["English", "Kiswahili", "Mathematics", "Community Service Learning"],
        "electives": ["History", "Geography", "Religious Education", "Business Studies"]
    },
    Track.ARTS_SPORTS: {
        "core": ["English", "Kiswahili", "Mathematics", "Community Service Learning"],
        "electives": ["Music", "Performing Arts", "Sports Science", "Visual Arts"]
    },
    Track.VOCATIONAL: {
        "core": ["English", "Kiswahili", "Mathematics", "Community Service Learning"],
        "electives": ["Home Science", "Agriculture", "Computer Science", "Drawing & Design"]
    }
}

class TrackSelectionService:
    @staticmethod
    def get_track_options():
        """Returns list of available tracks."""
        return [track.value for track in Track if track != Track.NONE]

    @staticmethod
    def get_subjects_for_track(track: Track) -> Dict[str, List[str]]:
        """Returns core and elective subjects for a given track."""
        return TRACK_SUBJECTS.get(track, {"core": [], "electives": []})

    @staticmethod
    def update_learner_track(learner_id: UUID, track: Track) -> Dict:
        """Updates the learner's profile with the selected track."""
        try:
            # 1. Update Profile
            response = supabase_client.table("profiles").update({"track": track.value}).eq("id", str(learner_id)).execute()
            
            # 2. Get Subjects for Track (For information/logging)
            subjects = TrackSelectionService.get_subjects_for_track(track)
            
            # In a full implementation, we might trigger an enrollment process here
            # to populate a 'learner_subjects' table.
            
            return response.data
        except Exception as e:
            print(f"Error updating track: {e}")
            raise e

    @staticmethod
    def get_learner_track(learner_id: UUID) -> Optional[Track]:
        """Retrieves the currently selected track for a learner."""
        try:
            response = supabase_client.table("profiles").select("track").eq("id", str(learner_id)).execute()
            if response.data and response.data[0].get("track"):
                try:
                    return Track(response.data[0]["track"])
                except ValueError:
                    # Handle case where database has invalid value
                    return Track.NONE
            return Track.NONE
        except Exception as e:
            print(f"Error getting learner track: {e}")
            return None

track_service = TrackSelectionService()
