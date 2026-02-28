
import sys
import os

# Add parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
import schemas

def verify_db_schema():
    db = SessionLocal()
    try:
        # Check if course_id exists in Question model
        print("Checking Question model columns...")
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        columns = [c['name'] for c in inspector.get_columns('questions')]
        if 'course_id' in columns:
            print("SUCCESS: course_id exists in questions table.")
        else:
            print("FAILURE: course_id NOT found in questions table.")
            
        # Check if assessment relationship works
        print("\nChecking Course-Question relationship...")
        new_course = models.Course(
            title="Test Assessment Course",
            description="Testing assessment linkage",
            instructor_id=1 # Assuming admin/instructor exists
        )
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        q = models.Question(
            questionText="Is this an assessment question?",
            course_id=new_course.id
        )
        db.add(q)
        db.commit()
        
        db.refresh(new_course)
        if len(new_course.assessment) > 0:
            print(f"SUCCESS: Course has {len(new_course.assessment)} assessment questions.")
        else:
            print("FAILURE: Assessment question not linked to course.")
            
        # Cleanup
        db.delete(q)
        db.delete(new_course)
        db.commit()
        print("\nCleanup successful.")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_db_schema()
