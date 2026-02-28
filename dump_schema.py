import sqlite3

def save_schema(filename):
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    with open(filename, 'w') as f:
        tables = ['users', 'enrolments', 'batches', 'questions']
        for table in tables:
            f.write(f"\n--- {table} ---\n")
            try:
                columns = cursor.execute(f"PRAGMA table_info({table});").fetchall()
                for col in columns:
                    f.write(f"{col}\n")
            except Exception as e:
                f.write(f"Error: {e}\n")
    conn.close()

if __name__ == "__main__":
    save_schema('schema_dump.txt')
