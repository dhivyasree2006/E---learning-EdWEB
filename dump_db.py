import sqlite3

def dump_ids():
    conn = sqlite3.connect('edweb.db')
    cur = conn.cursor()
    
    print("--- USERS ---")
    cur.execute("SELECT id, name, email, role FROM users")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- COURSES ---")
    cur.execute("SELECT id, title, instructor_id FROM courses")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- QUESTIONS ---")
    cur.execute("SELECT id, course_id, difficulty, questionText FROM questions LIMIT 10")
    for row in cur.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    dump_ids()
