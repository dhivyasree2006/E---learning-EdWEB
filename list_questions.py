from sqlalchemy.orm import Session
from database import SessionLocal
import models

def list_questions():
    db = SessionLocal()
    course_id = 1
    questions = db.query(models.Question).filter(models.Question.course_id == course_id).all()
    print(f"--- Questions for Course {course_id} ---")
    for q in questions:
        print(f"ID: {q.id}, Diff: {q.difficulty}, Type: {q.questionType}")
        if q.questionType == "mcq":
            print(f"  Options: {[o.text for o in q.options]}")
            print(f"  Correct Index: {q.correctOptionIndex}")
        else:
            print(f"  Correct Text: {q.correctAnswerText}")
    db.close()

if __name__ == "__main__":
    list_questions()
