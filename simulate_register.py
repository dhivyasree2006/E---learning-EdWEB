import models, database, auth, schemas
from sqlalchemy.orm import Session
from datetime import datetime

def test_registration():
    db = database.SessionLocal()
    try:
        user_data = schemas.UserCreate(
            name="Test User",
            email="test_unique_" + str(int(datetime.utcnow().timestamp())) + "@example.com",
            password="testpassword",
            role="learner"
        )
        
        print(f"Attempting to register: {user_data.email}")
        
        db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
        if db_user:
            print("Error: Email already registered")
            return
        
        hashed_password = auth.get_password_hash(user_data.password)
        new_user = models.User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Success! Registered user with ID: {new_user.id}")
        
    except Exception as e:
        import traceback
        print(f"Registration Failed: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_registration()
