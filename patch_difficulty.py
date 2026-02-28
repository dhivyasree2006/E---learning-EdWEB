import sqlite3

def patch_difficulty():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    
    print("Patching database: Adding 'difficulty' to 'questions' table...")
    
    try:
        cursor.execute("ALTER TABLE questions ADD COLUMN difficulty VARCHAR DEFAULT 'medium'")
        print("Success: Column 'difficulty' added.")
    except sqlite3.OperationalError:
        print("Note: Column 'difficulty' already exists or other database error.")
        
    conn.commit()
    conn.close()
    print("Database patch complete.")

if __name__ == "__main__":
    patch_difficulty()
