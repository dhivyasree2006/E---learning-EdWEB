import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_adaptive_flow():
    # 1. Login to get token
    login_data = {"username": "miru@gmail.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get a course ID
    course_id = 2 # AI Testing Course
    
    # Ensure enrollment (optional but safe)
    requests.post(f"{BASE_URL}/courses/{course_id}/enroll", headers=headers)

    # 3. Start Adaptive Quiz
    print("\n--- Starting Adaptive Quiz ---")
    resp = requests.post(f"{BASE_URL}/quizzes/{course_id}/adaptive/start", headers=headers)
    print("Start Response Status:", resp.status_code)
    if resp.status_code != 200:
        print("Error:", resp.text)
        return
    
    start_data = resp.json()
    if start_data.get("completed"):
        print("Course assessment already completed.")
        return

    first_q = start_data.get("question")
    if not first_q:
        print("No question returned.")
        print(json.dumps(start_data, indent=2))
        return
        
    print(f"First Question ID: {first_q['id']} (Difficulty: {first_q['difficulty']})")
    print(f"Question: {first_q['questionText']}")
    
    # 4. Get Next Question (Correct Answer -> Should go to Hard)
    print("\n--- Correct Answer -> Harder ---")
    next_payload = {
        "answered_ids": [first_q["id"]],
        "last_answer": first_q.get("correctOptionIndex", 0), # Mock correct
        "last_difficulty": first_q["difficulty"]
    }
    resp = requests.post(f"{BASE_URL}/quizzes/{course_id}/adaptive/next", json=next_payload, headers=headers)
    print("Next Response Status:", resp.status_code)
    if resp.status_code != 200:
        print("Error:", resp.text)
        return

    next_data = resp.json()
    if not next_data.get("finished"):
        second_q = next_data["question"]
        print(f"Second Question ID: {second_q['id']} (Difficulty: {second_q['difficulty']})")
        print(f"Question: {second_q['questionText']}")
    else:
        print("Quiz finished unexpectedly or no more questions.")

    # 5. Get Next Question (Wrong Answer -> Should go to Easy)
    print("\n--- Wrong Answer -> Easier ---")
    next_payload = {
        "answered_ids": [first_q["id"], second_q["id"]],
        "last_answer": 99, # Wrong answer
        "last_difficulty": second_q["difficulty"]
    }
    resp = requests.post(f"{BASE_URL}/quizzes/{course_id}/adaptive/next", json=next_payload, headers=headers)
    next_data = resp.json()
    if not next_data.get("finished"):
        third_q = next_data["question"]
        print(f"Third Question ID: {third_q['id']} (Difficulty: {third_q['difficulty']})")
        print(f"Question: {third_q['questionText']}")
    else:
        print("Quiz finished or no more questions.")

if __name__ == "__main__":
    # Ensure server is running or mock if needed.
    # For actually running, we rely on the user's environment.
    try:
        test_adaptive_flow()
    except Exception as e:
        print("Testing Error:", e)
