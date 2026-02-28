import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_assessment_access():
    print("--- Verifying Assessment Access Fix ---")
    
    # 1. Login as Instructor
    print("1. Logging in as instructor...")
    inst_login = {"username": "instructor@demo.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=inst_login)
    if resp.status_code != 200:
        print("Registering instructor...")
        requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Instructor", "email": "instructor@demo.com", "password": "password123", "role": "instructor"
        })
        resp = requests.post(f"{BASE_URL}/auth/login", json=inst_login)
    
    inst_token = resp.json()["access_token"]
    inst_headers = {"Authorization": f"Bearer {inst_token}"}
    
    # 2. Create a Course with Assessment
    print("2. Creating course with assessment...")
    course_data = {
        "title": "Verif Assessment Course",
        "description": "Testing assessment access",
        "thumbnail": "",
        "price": 0,
        "status": "Published",
        "assessment": [
            {
                "questionText": "What is 2+2?",
                "questionType": "mcq",
                "options": [{"text": "3"}, {"text": "4"}],
                "correctOptionIndex": 1
            }
        ]
    }
    resp = requests.post(f"{BASE_URL}/courses", json=course_data, headers=inst_headers)
    course_id = resp.json()["id"]
    print(f"Course created with ID: {course_id}")
    
    # 3. Login as Learner
    print("3. Logging in as learner...")
    learner_login = {"username": "learner@demo.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=learner_login)
    if resp.status_code != 200:
         requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Learner", "email": "learner@demo.com", "password": "password123", "role": "learner"
        })
         resp = requests.post(f"{BASE_URL}/auth/login", json=learner_login)
    
    learner_token = resp.json()["access_token"]
    learner_headers = {"Authorization": f"Bearer {learner_token}"}
    
    # 4. Try to fetch assessment WITHOUT enrollment (Should fail)
    print("4. Fetching assessment WITHOUT enrollment...")
    resp = requests.get(f"{BASE_URL}/quizzes/{course_id}", headers=learner_headers)
    if resp.status_code == 403:
        print("SUCCESS: Access denied for unenrolled learner.")
    else:
        print(f"FAILURE: Expected 403, got {resp.status_code}")
        
    # 5. Enroll learner
    print("5. Enrolling learner...")
    requests.post(f"{BASE_URL}/courses/{course_id}/enroll", headers=learner_headers)
    
    # 6. Try to fetch assessment WITH enrollment (Should succeed)
    print("6. Fetching assessment WITH enrollment...")
    resp = requests.get(f"{BASE_URL}/quizzes/{course_id}", headers=learner_headers)
    if resp.status_code == 200:
        data = resp.json()
        if len(data["questions"]) > 0:
            print(f"SUCCESS: Retrieved {len(data['questions'])} questions.")
        else:
            print("FAILURE: No questions returned.")
    else:
        print(f"FAILURE: Expected 200, got {resp.status_code}: {resp.text}")
        
    # 7. Cleanup
    print("7. Cleaning up...")
    requests.delete(f"{BASE_URL}/courses/{course_id}", headers=inst_headers)
    print("Cleanup done.")

if __name__ == "__main__":
    test_assessment_access()
