import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_adaptive():
    # 1. Login as learner
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"username": "learner@demo.com", "password": "password123"})
    if login_res.status_code != 200:
        # Try without /api/ prefix if it fails
        login_res = requests.post(f"{BASE_URL}/auth/login", json={"username": "learner@demo.com", "password": "password123"})
    
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.status_code} - {login_res.text}")
        return
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Course ID
    course_id = 1 
    
    # 3. Start adaptive quiz
    print(f"Starting adaptive quiz for course {course_id}...")
    start_res = requests.post(f"{BASE_URL}/quizzes/{course_id}/adaptive/start", headers=headers)
    if start_res.status_code != 200:
        print(f"Start failed: {start_res.text}")
        return
    
    q1 = start_res.json()["question"]
    print(f"Q1 (ID: {q1['id']}, Difficulty: {q1.get('difficulty')}): {q1['questionText'][:50]}...")
    
    # 4. Simulate a CORRECT answer (We need to find the correct index)
    # Since we can't see it on backend response for learners, let's assume we know it or just test the transition.
    # I'll use a script to check the correct answer for Q1 on the backend.
    
    last_difficulty = q1.get('difficulty', 'medium')
    
    # FOR TESTING: We'll just send an answer. The backend will evaluate it.
    # If we want a CORRECT answer, we'd need to know it. 
    # Let's assume we'll just test the call structure first.
    
    print(f"Answering Q1...")
    next_res = requests.post(f"{BASE_URL}/quizzes/{course_id}/adaptive/next", headers=headers, json={
        "answered_ids": [q1['id']],
        "last_answer": 0, # Assuming 0 might be right or we just see it change
        "last_difficulty": last_difficulty
    })
    
    if next_res.status_code == 200:
        next_data = next_res.json()
        if not next_data.get("finished"):
            q2 = next_data["question"]
            print(f"Q2 (ID: {q2['id']}, Difficulty: {q2.get('difficulty')}): {q2['questionText'][:50]}...")
            print(f"Success: Transitioned to Q2.")
        else:
            print("Quiz finished or no more questions.")
    else:
        print(f"Next call failed: {next_res.status_code} - {next_res.text}")

if __name__ == "__main__":
    test_adaptive()

if __name__ == "__main__":
    test_adaptive()
