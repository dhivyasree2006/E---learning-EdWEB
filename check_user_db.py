import sqlite3

def check_user_and_schema():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    
    # Check for the user from the screenshot
    print("\n--- Checking for user gow@gmail.com ---")
    user = cursor.execute("SELECT id, email, role FROM users WHERE email='gow@gmail.com'").fetchone()
    print(f"User found: {user}")
    
    # Double check enrolments schema
    print("\n--- enrolments schema ---")
    columns = cursor.execute("PRAGMA table_info(enrolments)").fetchall()
    for col in columns:
        print(col)
        
    conn.close()

if __name__ == "__main__":
    check_user_and_schema()
