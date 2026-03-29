import os
import sys
from app.core.database import supabase_client

# Add parent directory to path to allow imports if run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_or_create_subject(name: str, grade: str):
    print(f"Checking subject: {name} ({grade})...")
    try:
        # Check if exists
        response = supabase_client.table("subjects").select("id").eq("name", name).eq("grade_level", grade).execute()
        if response.data:
            print(f"  - Exists: {response.data[0]['id']}")
            return response.data[0]["id"]
        
        # Create
        print(f"  - Creating new subject...")
        response = supabase_client.table("subjects").insert({"name": name, "grade_level": grade}).execute()
        if response.data:
            print(f"  - Created: {response.data[0]['id']}")
            return response.data[0]["id"]
        else:
            print(f"  - Failed to create (no data returned)")
            return None
    except Exception as e:
        print(f"  - Error: {e}")
        return None

def init_jss_subjects():
    print("Initializing Junior Secondary School (JSS) Subjects for Grades 7-9...")
    
    grades = ["Grade 7", "Grade 8", "Grade 9"]
    subjects = [
        "English",
        "Kiswahili",
        "Mathematics",
        "Integrated Science",
        "Pre-Technical Studies",
        "Social Studies",
        "Business Studies",
        "Creative Arts",
        "Physical & Health Ed"
    ]
    
    count = 0
    total = len(grades) * len(subjects)
    
    for grade in grades:
        print(f"\n--- {grade} ---")
        for subject in subjects:
            result = get_or_create_subject(subject, grade)
            if result:
                count += 1
                
    print(f"\nInitialization complete. {count}/{total} subjects verified/created.")

if __name__ == "__main__":
    init_jss_subjects()
