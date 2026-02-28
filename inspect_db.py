import sqlite3

def inspect():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(f"Tables: {tables}")
    
    for table in tables:
        table_name = table[0]
        print(f"\nSchema for {table_name}:")
        schema = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        for col in schema:
            print(f" - {col}")
    
    conn.close()

if __name__ == "__main__":
    inspect()
