
from database import SessionLocal
import models
import schemas
from datetime import datetime

def verify():
    db = SessionLocal()
    try:
        print("Creating test course...")
        # Create a test instructor if doesn't exist
        instructor = db.query(models.User).filter(models.User.role == "instructor").first()
        if not instructor:
            print("No instructor found, creating one...")
            instructor = models.User(
                name="Test Instructor",
                email="test_instructor@example.com",
                password="hashed_password",
                role="instructor"
            )
            db.add(instructor)
            db.commit()
            db.refresh(instructor)

        # Simulate course data
        course_data = {
            "title": "Verification Course",
            "description": "A course to verify the fix",
            "status": "Published",
            "instructor_id": instructor.id,
            "modules": [
                {
                    "title": "Module 1",
                    "quiz": [
                        {
                            "questionText": "What is 2+2?",
                            "questionType": "mcq",
                            "correctOptionIndex": 0,
                            "options": [{"text": "4"}, {"text": "5"}]
                        }
                    ]
                }
            ],
            "assessment": [
                {
                    "questionText": "Describe the universe.",
                    "questionType": "descriptive",
                    "correctAnswerText": "It's big."
                }
            ]
        }

        # Create course in DB manually (similar to main.py logic)
        new_course = models.Course(
            title=course_data["title"],
            description=course_data["description"],
            status=course_data["status"],
            instructor_id=course_data["instructor_id"]
        )
        db.add(new_course)
        db.commit()
        db.refresh(new_course)

        for mod in course_data["modules"]:
            new_mod = models.Module(title=mod["title"], course_id=new_course.id)
            db.add(new_mod)
            db.commit()
            db.refresh(new_mod)
            for q in mod["quiz"]:
                new_q = models.Question(
                    questionText=q["questionText"],
                    questionType=q["questionType"],
                    correctOptionIndex=q["correctOptionIndex"],
                    module_id=new_mod.id
                )
                db.add(new_q)
                db.commit()
                db.refresh(new_q)
                for opt in q["options"]:
                    db.add(models.QuestionOption(text=opt["text"], question_id=new_q.id))

        for q in course_data["assessment"]:
            new_q = models.Question(
                questionText=q["questionText"],
                questionType=q["questionType"],
                correctAnswerText=q["correctAnswerText"],
                course_id=new_course.id
            )
            db.add(new_q)
            db.commit()
            db.refresh(new_q)

        db.commit()
        print(f"Course created with ID: {new_course.id}")

        # Verify retrieval
        print("Verifying data in DB...")
        retrieved_course = db.query(models.Course).filter(models.Course.id == new_course.id).first()
        assert retrieved_course.title == "Verification Course"
        assert retrieved_course.status == "Published"
        
        # Check module question
        mod_q = db.query(models.Question).filter(models.Question.module_id == retrieved_course.modules[0].id).first()
        print(f"Module Question Type: {mod_q.questionType}")
        assert mod_q.questionType == "mcq"

        # Check assessment question
        ass_q = db.query(models.Question).filter(models.Question.course_id == retrieved_course.id).first()
        print(f"Assessment Question Type: {ass_q.questionType}")
        print(f"Assessment Correct Answer: {ass_q.correctAnswerText}")
        assert ass_q.questionType == "descriptive"
        assert ass_q.correctAnswerText == "It's big."

        print("Verification successful!")

    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify()
