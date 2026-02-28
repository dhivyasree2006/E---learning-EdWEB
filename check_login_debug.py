import models, database, auth
import bcrypt

def check_login():
    db = next(database.get_db())
    print("--- Database Check ---")
    users = db.query(models.User).all()
    if not users:
        print("No users found in database!")
        return

    for user in users:
        print(f"\nUser: {user.email}")
        print(f"Role: {user.role}")
        
        # Test password 'password123'
        test_pass = "password123"
        try:
            match = auth.verify_password(test_pass, user.password)
            print(f"Match with 'password123': {match}")
        except Exception as e:
            print(f"Error verifying password: {e}")

if __name__ == "__main__":
    check_login()
