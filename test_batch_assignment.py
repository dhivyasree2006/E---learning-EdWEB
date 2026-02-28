import requests
import json

BASE_URL = "http://127.0.0.1:8005"

def log(msg):
    print(msg)
    with open("test_batch_result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_batch_assignment():
    with open("test_batch_result.log", "w", encoding="utf-8") as f:
        f.write("Running test_batch_assignment...\n")

    try:
        # 1. Login as Instructor
        inst_data = {"username": "instructor@demo.com", "password": "password123"}
        log(f"Logging in as {inst_data['username']}...")
        resp = requests.post(f"{BASE_URL}/auth/login", json=inst_data)
        if resp.status_code != 200:
            # Register if not exists
            log("Instructor login failed, registering...")
            reg_data = {"name": "Demo Instructor", "email": "instructor@demo.com", "password": "password123", "role": "instructor"}
            requests.post(f"{BASE_URL}/auth/register", json=reg_data)
            resp = requests.post(f"{BASE_URL}/auth/login", json=inst_data)
        
        inst_token = resp.json()["access_token"]
        inst_headers = {"Authorization": f"Bearer {inst_token}"}
        log("Instructor login successful.")

        # 2. Login/Register as Learner
        learner_data = {"username": "learner@demo.com", "password": "password123"}
        log(f"Logging in as {learner_data['username']}...")
        resp = requests.post(f"{BASE_URL}/auth/login", json=learner_data)
        if resp.status_code != 200:
            log("Learner login failed, registering...")
            reg_data = {"name": "Demo Learner", "email": "learner@demo.com", "password": "password123", "role": "learner"}
            requests.post(f"{BASE_URL}/auth/register", json=reg_data)
            resp = requests.post(f"{BASE_URL}/auth/login", json=learner_data)
        
        learner_user = resp.json()["user"]
        learner_id = learner_user["id"]
        learner_token = resp.json()["access_token"]
        learner_headers = {"Authorization": f"Bearer {learner_token}"}
        log(f"Learner login successful. ID: {learner_id}")

        # 3. Create a Course if needed
        log("Fetching instructor courses...")
        resp = requests.get(f"{BASE_URL}/courses/my-courses", headers=inst_headers)
        courses = resp.json()
        if not courses:
            log("No courses found, creating one...")
            course_data = {
                "title": "Test Course",
                "description": "Test Description",
                "price": 0.0,
                "status": "Published",
                "modules": []
            }
            resp = requests.post(f"{BASE_URL}/courses", json=course_data, headers=inst_headers)
            course_id = resp.json()["id"]
        else:
            course_id = courses[0]["id"]
        
        log(f"Using Course ID: {course_id}")

        # 4. Enroll Learner in Course
        log(f"Enrolling learner {learner_id} in course {course_id}...")
        requests.post(f"{BASE_URL}/courses/{course_id}/enroll", headers=learner_headers)

        # 5. Create or Get a Batch
        log("Fetching batches...")
        resp = requests.get(f"{BASE_URL}/batches", headers=inst_headers)
        batches = resp.json()
        batch_id = None
        for b in batches:
            if b["course_id"] == course_id:
                batch_id = b["id"]
                break
        
        if not batch_id:
            log("Creating a new batch...")
            batch_data = {
                "name": "Test Batch",
                "course_id": course_id,
                "start_time": None,
                "end_time": None
            }
            resp = requests.post(f"{BASE_URL}/batches", json=batch_data, headers=inst_headers)
            batch_id = resp.json()["id"]
        
        log(f"Using Batch ID: {batch_id}")

        # 6. Assign Student to Batch
        log(f"Assigning student {learner_id} to batch {batch_id}...")
        resp = requests.post(f"{BASE_URL}/batches/{batch_id}/students", json=[learner_id], headers=inst_headers)
        log(f"Assignment response: {resp.status_code} - {resp.text}")

        # 7. Verify Assignment
        log("Verifying assignment...")
        resp = requests.get(f"{BASE_URL}/batches", headers=inst_headers)
        batches = resp.json()
        target_batch = next((b for b in batches if b["id"] == batch_id), None)
        
        if target_batch:
            log(f"Batch Students: {json.dumps(target_batch.get('students', []), indent=2)}")
            student_ids = [s["id"] for s in target_batch.get("students", [])]
            if learner_id in student_ids:
                log("SUCCESS: Student found in batch students list!")
            else:
                log("FAILURE: Student NOT found in batch students list.")
        else:
            log("FAILURE: Batch not found in list.")

    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    test_batch_assignment()
