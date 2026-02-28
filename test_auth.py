import sqlite3
import auth
import models

def test():
    try:
        conn = sqlite3.connect('edweb.db')
        c = conn.cursor()
        c.execute('SELECT email, password FROM users WHERE email="instructor@edweb.com"')
        row = c.fetchone()
        conn.close()

        if not row:
            print("User not found in DB")
            return

        email, hashed = row
        print(f"User: {email}")
        print(f"Stored Hash: {hashed}")
        
        test_pass = "password123"
        is_valid = auth.verify_password(test_pass, hashed)
        print(f"Verification of '{test_pass}': {is_valid}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
