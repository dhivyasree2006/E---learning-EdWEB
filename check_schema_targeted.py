import sqlite3

def check_table(table_name):
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    try:
        print(f"\n--- {table_name} ---")
        columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error checking {table_name}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_table('users')
    check_table('enrolments')
    check_table('batches')
    check_table('questions')
