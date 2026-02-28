import models, database, auth
import sys

def seed():
    try:
        print(f"--- Database URL: {database.engine.url} ---")
        # Ensure tables are created
        models.Base.metadata.create_all(bind=database.engine)
        db = next(database.get_db())
        
        # 1. Prepare demo users
        demo_users = [
            {
                "name": "Dr. Jane Smith",
                "email": "instructor@edweb.com",
                "password": "password123",
                "role": "instructor"
            },
            {
                "name": "Miru Learner",
                "email": "miru@gmail.com",
                "password": "password123",
                "role": "learner"
            }
        ]

        print("--- Starting Seeding ---")
        for user_data in demo_users:
            user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            if not user:
                user = models.User(
                    name=user_data["name"],
                    email=user_data["email"],
                    password=auth.get_password_hash(user_data["password"]),
                    role=user_data["role"]
                )
                db.add(user)
                print(f"[SEED] Created: {user_data['email']}")
            else:
                user.password = auth.get_password_hash(user_data["password"])
                user.name = user_data["name"]
                user.role = user_data["role"]
                print(f"[SEED] Updated: {user_data['email']}")
        
        db.commit()
        print("[SEED] Users committed.")

        # 2. Courses (Removed static seeding)
        print("[SEED] Static course seeding disabled.")
        
        print("[SEED] Seeding SUCCESS.")
    except Exception as e:
        print(f"[SEED ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed()
