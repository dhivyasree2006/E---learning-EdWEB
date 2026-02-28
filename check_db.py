import sqlite3

def check_users():
    conn = sqlite3.connect('edweb.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email, role FROM users')
    users = cursor.fetchall()
    print(f"Users: {users}")
    
    # Ensure some questions have varied difficulty for course 1
    cursor.execute("UPDATE questions SET difficulty='easy' WHERE id IN (SELECT id FROM questions WHERE course_id=1 LIMIT 2)")
    cursor.execute("UPDATE questions SET difficulty='medium' WHERE id IN (SELECT id FROM questions WHERE course_id=1 AND difficulty!='easy' LIMIT 2)")
    cursor.execute("UPDATE questions SET difficulty='hard' WHERE id IN (SELECT id FROM questions WHERE course_id=1 AND difficulty NOT IN ('easy', 'medium') LIMIT 2)")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    check_users()
