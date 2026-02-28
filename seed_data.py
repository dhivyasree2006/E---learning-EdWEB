import models
import database
import auth
import os

def seed():
    # Initialize DB if not exists
    db = database.get_db_data()
    
    # Check if instructor exists
    instructor = next((u for u in db["users"] if u["email"] == "instructor@edweb.com"), None)
    if not instructor:
        instructor_id = max([u["id"] for u in db["users"]] + [0]) + 1
        instructor = {
            "id": instructor_id,
            "name": "Dr. Jane Smith",
            "email": "instructor@edweb.com",
            "password": auth.get_password_hash("password123"),
            "role": "instructor",
            "created_at": models.UserResponse(name="Dr. Jane Smith", email="instructor@edweb.com", id=instructor_id).created_at
        }
        db["users"].append(instructor)
        print(f"Created instructor: {instructor['email']}")

    # Check if courses exist (Disabled static seeding)
    print("Static course seeding disabled in seed_data.py")

    database.save_db_data(db)

if __name__ == "__main__":
    seed()
