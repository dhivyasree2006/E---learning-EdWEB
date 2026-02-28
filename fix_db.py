import sqlite3

def fix_db():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    
    print("Fixing database schema...")
    
    # Add start_time and end_time to batches
    try:
        cursor.execute("ALTER TABLE batches ADD COLUMN start_time DATETIME")
        print("Added start_time to batches")
    except sqlite3.OperationalError:
        print("start_time already exists or table not found")
        
    try:
        cursor.execute("ALTER TABLE batches ADD COLUMN end_time DATETIME")
        print("Added end_time to batches")
    except sqlite3.OperationalError:
        print("end_time already exists")

    # Create certificates table if missing
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_id INTEGER,
                certificate_code VARCHAR UNIQUE,
                issued_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(course_id) REFERENCES courses(id)
            )
        """)
        print("Ensured certificates table exists")
    except Exception as e:
        print(f"Error creating certificates table: {e}")

    conn.commit()
    conn.close()
    print("Database fix complete.")

if __name__ == "__main__":
    fix_db()
