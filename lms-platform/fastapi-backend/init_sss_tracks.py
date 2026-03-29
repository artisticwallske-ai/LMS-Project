import os
import sys
from app.core.database import supabase_client

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_or_create_subject(name: str, grade: str):
    print(f"Checking subject: {name} ({grade})...")
    try:
        response = supabase_client.table("subjects").select("id").eq("name", name).eq("grade_level", grade).execute()
        if response.data:
            print(f"  - Exists: {response.data[0]['id']}")
            return response.data[0]["id"]
        
        response = supabase_client.table("subjects").insert({"name": name, "grade_level": grade}).execute()
        if response.data:
            print(f"  - Created: {response.data[0]['id']}")
            return response.data[0]["id"]
        return None
    except Exception as e:
        print(f"  - Error: {e}")
        return None

def init_sss_subjects():
    print("Initializing Senior Secondary School (SSS) Subjects for Grades 10-12...")
    
    grades = ["Grade 10", "Grade 11", "Grade 12"]
    
    # 4 Compulsory Core
    core_subjects = ["English", "Kiswahili", "Mathematics", "Community Service Learning"]
    
    # Electives per Track (Subset for MVP)
    # STEM
    stem_electives = ["Physics", "Chemistry", "Biology", "Computer Science"]
    # Social Sciences
    soc_electives = ["History", "Geography", "Religious Education", "Business Studies"]
    # Arts & Sports
    arts_electives = ["Music", "Performing Arts", "Sports Science", "Visual Arts"]
    # Vocational
    voc_electives = ["Home Science", "Agriculture", "Computer Science", "Drawing & Design"]
    
    all_subjects = list(set(core_subjects + stem_electives + soc_electives + arts_electives + voc_electives))
    
    count = 0
    
    for grade in grades:
        print(f"\n--- {grade} ---")
        for subject in all_subjects:
            result = get_or_create_subject(subject, grade)
            if result:
                count += 1
                
    print(f"\nInitialization complete. {count} subjects verified/created.")

if __name__ == "__main__":
    init_sss_subjects()
