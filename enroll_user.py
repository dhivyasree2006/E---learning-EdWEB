from sqlalchemy.orm import Session
from database import SessionLocal
import models

def enroll_user():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == "learner@demo.com").first()
    if not user:
        print("User not found")
        return
    
    course_id = 1
    # Check if already enrolled
    enrollment = db.query(models.Enrolment).filter(
        models.Enrolment.user_id == user.id,
        models.Enrolment.course_id == course_id
    ).first()
    
    if not enrollment:
        enrollment = models.Enrolment(user_id=user.id, course_id=course_id)
        db.add(enrollment)
        db.commit()
        print(f"Enrolled {user.email} in Course {course_id}")
    else:
        print(f"{user.email} is already enrolled in Course {course_id}")
    db.close()

if __name__ == "__main__":
    enroll_user()
