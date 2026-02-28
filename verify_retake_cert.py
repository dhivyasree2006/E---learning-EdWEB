import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_retake_prevention():
    # 1. Login (assuming we have a test user, let's try to register or use existing)
    login_data = {"username": "learner@example.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print("Login failed. Registration might be needed.")
        # Try registration
        reg_data = {"email": "learner@example.com", "password": "password123", "name": "Test Learner", "role": "learner"}
        requests.post(f"{BASE_URL}/auth/register", json=reg_data)
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Try to find a course
    courses = requests.get(f"{BASE_URL}/courses", headers=headers).json()
    if not courses:
        print("No courses found. Please create a course first.")
        return
    
    course_id = courses[0]["id"]
    print(f"Testing with Course ID: {course_id}")

    # 3. Enroll if not already
    requests.post(f"{BASE_URL}/courses/{course_id}/enroll", headers=headers)

    # 4. Attempt to submit assessment
    submit_data = {
        "answers": [0] * 20, # Dummy answers
        "is_adaptive": False
    }
    
    print("Submitting first assessment...")
    resp1 = requests.post(f"{BASE_URL}/quizzes/{course_id}/submit", json=submit_data, headers=headers)
    print(f"First Submission Status: {resp1.status_code}")
    
    print("Attempting second assessment (should fail)...")
    resp2 = requests.post(f"{BASE_URL}/quizzes/{course_id}/submit", json=submit_data, headers=headers)
    print(f"Second Submission Status: {resp2.status_code}")
    print(f"Second Submission Response: {resp2.json()}")
    
    if resp2.status_code == 400:
        print("SUCCESS: Retake prevention worked!")
    else:
        print("FAILURE: Retake prevention failed or returned different status.")

    # 5. Check certificates
    print("Checking certificates...")
    certs = requests.get(f"{BASE_URL}/api/certificates/me", headers=headers).json()
    print(f"Certificates found: {len(certs)}")
    # 6. Verify result retrieval
    print("Verifying result retrieval for completed assessment...")
    resp_get = requests.get(f"{BASE_URL}/quizzes/{course_id}", headers=headers)
    print(f"GET assessment status: {resp_get.status_code}")
    if resp_get.status_code == 200:
        data = resp_get.json()
        if data.get("completed"):
            score = data.get("score")
            total = data.get("totalQuestions")
            print(f"SUCCESS: Result retrieved! Score: {score}/{total}")
            
            if score > total:
                print("FAILED: Score is likely a percentage or incorrect!")
            else:
                print("SUCCESS: Score is a valid raw count.")
                
            if "userAnswers" in data:
                print("SUCCESS: userAnswers found!")
            else:
                print("FAILED: userAnswers missing!")

            if "certificate" in data:
                print(f"SUCCESS: Certificate status: {data['certificate']}")
        else:
            print("FAILURE: Endpoint returned questions instead of result for completed assessment.")
    else:
        print(f"FAILURE: Endpoint returned error status: {resp_get.status_code}")

if __name__ == "__main__":
    test_retake_prevention()
