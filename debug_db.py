import models, database
from sqlalchemy.orm import Session

def test():
    try:
        db = next(database.get_db())
        print("Connected to DB")
        users = db.query(models.User).all()
        print(f"Users found: {len(users)}")
    except Exception as e:
        print(f"Error during User query: {e}")

    try:
        db = next(database.get_db())
        courses = db.query(models.Course).all()
        print(f"Courses found: {len(courses)}")
    except Exception as e:
        print(f"Error during Course query: {e}")

if __name__ == "__main__":
    test()
