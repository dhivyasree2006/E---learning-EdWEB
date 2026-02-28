
import sqlite3
import os

def migrate():
    db_path = 'edweb.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration...")
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add questionType if missing
        if 'questionType' not in columns:
            print("Adding questionType column to questions table...")
            cursor.execute("ALTER TABLE questions ADD COLUMN questionType TEXT DEFAULT 'mcq'")
        else:
            print("questionType column already exists.")

        # Add correctAnswerText if missing
        if 'correctAnswerText' not in columns:
            print("Adding correctAnswerText column to questions table...")
            cursor.execute("ALTER TABLE questions ADD COLUMN correctAnswerText TEXT")
        else:
            print("correctAnswerText column already exists.")

        # Add course_id if missing
        if 'course_id' not in columns:
            print("Adding course_id column to questions table...")
            cursor.execute("ALTER TABLE questions ADD COLUMN course_id INTEGER REFERENCES courses(id)")
        else:
            print("course_id column already exists.")

        # Add start_time and end_time to batches if missing
        cursor.execute("PRAGMA table_info(batches)")
        batch_columns = [col[1] for col in cursor.fetchall()]

        if 'start_time' not in batch_columns:
            print("Adding start_time column to batches table...")
            cursor.execute("ALTER TABLE batches ADD COLUMN start_time DATETIME")
        
        if 'end_time' not in batch_columns:
            print("Adding end_time column to batches table...")
            cursor.execute("ALTER TABLE batches ADD COLUMN end_time DATETIME")

        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
