import sqlite3
import auth
from datetime import datetime

def create_test_user():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    
    password = "password123"
    # Use the project's own hashing logic
    hashed_pw = auth.get_password_hash(password)
    email = "test_learner@example.com"
    now = datetime.utcnow().isoformat()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET password=?, created_at=? WHERE email=?", (hashed_pw, now, email))
        print(f"User {email} updated successfully.")
    else:
        cursor.execute("INSERT INTO users (email, password, name, role, created_at) VALUES (?, ?, ?, ?, ?)", 
                       (email, hashed_pw, "Test Learner", "learner", now))
        print(f"User {email} created successfully.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_test_user()
