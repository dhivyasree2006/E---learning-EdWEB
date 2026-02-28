import sqlite3
import os

def migrate():
    db_path = 'edweb.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Add accessibility_enabled to enrolments
    try:
        print("Checking enrolments table...")
        columns = [col[1] for col in cursor.execute("PRAGMA table_info(enrolments)").fetchall()]
        if 'accessibility_enabled' not in columns:
            print("Adding accessibility_enabled to enrolments...")
            cursor.execute("ALTER TABLE enrolments ADD COLUMN accessibility_enabled BOOLEAN DEFAULT 0")
            print("Successfully added accessibility_enabled.")
        else:
            print("accessibility_enabled already exists in enrolments.")
    except Exception as e:
        print(f"Error migrating enrolments: {e}")

    # 2. Verify batches and questions just in case, though dump showed them present
    # We'll just do a safety check
    try:
        columns = [col[1] for col in cursor.execute("PRAGMA table_info(batches)").fetchall()]
        for col in ['start_time', 'end_time']:
            if col not in columns:
                print(f"Adding {col} to batches...")
                cursor.execute(f"ALTER TABLE batches ADD COLUMN {col} DATETIME")
    except Exception as e:
        print(f"Error checking batches: {e}")

    try:
        columns = [col[1] for col in cursor.execute("PRAGMA table_info(questions)").fetchall()]
        if 'questionType' not in columns:
            print("Adding questionType to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN questionType VARCHAR DEFAULT 'mcq'")
        if 'difficulty' not in columns:
            print("Adding difficulty to questions...")
            cursor.execute("ALTER TABLE questions ADD COLUMN difficulty VARCHAR DEFAULT 'medium'")
    except Exception as e:
        print(f"Error checking questions: {e}")

    conn.commit()
    conn.close()
    print("Migration check complete.")

if __name__ == "__main__":
    migrate()
