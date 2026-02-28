import requests
import json

BASE_URL = "http://localhost:8100" # Based on logs usually 8100 or 8000

def test_accessibility_flow():
    # 1. Login as Instructor
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "instructor@example.com",
        "password": "password123"
    })
    
    if login_res.status_code != 200:
        print(f"Instructor login failed ({login_res.status_code}). Ensure server is running and user exists.")
        return

    instructor_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # 2. Get Learners to find an enrolment_id
    learners_res = requests.get(f"{BASE_URL}/courses/my-learners", headers=headers)
    if learners_res.status_code != 200:
        print("Failed to fetch learners")
        return
    
    learners = learners_res.json()
    if not learners:
        print("No learners found for this instructor.")
        return
    
    target_learner = learners[0]
    enrolment_id = target_learner.get("enrolment_id")
    learner_email = target_learner["email"]
    
    if not enrolment_id:
        print("Enrolment ID missing in learner data")
        return

    print(f"Testing with Learner: {learner_email}, Enrolment ID: {enrolment_id}")

    # 3. Toggle Accessibility ON
    toggle_res = requests.put(
        f"{BASE_URL}/api/instructor/enrolments/{enrolment_id}/accessibility",
        headers=headers,
        json={"accessibility_enabled": True}
    )
    print(f"Toggle ON Result: {toggle_res.status_code} - {toggle_res.json()}")

if __name__ == "__main__":
    test_accessibility_flow()
