import sqlite3
import os

def patch_enrolments():
    # Use relative path from backend directory or absolute path
    db_path = os.path.join(os.path.dirname(__file__), 'edweb.db')
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print(f"Patching database at {db_path}...")
        
        # Check existing columns for enrolments
        cursor.execute("PRAGMA table_info(enrolments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add accessibility_enabled if missing
        if 'accessibility_enabled' not in columns:
            print("Adding accessibility_enabled column to enrolments table...")
            cursor.execute("ALTER TABLE enrolments ADD COLUMN accessibility_enabled BOOLEAN DEFAULT 0")
            print("Column added successfully.")
        else:
            print("accessibility_enabled column already exists.")

        conn.commit()
    except Exception as e:
        print(f"Patch failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch_enrolments()
