import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(msg)

def verify_visibility():
    # 1. Setup - Login as Instructor
    inst_login = {"username": "instructor@demo.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=inst_login)
    if resp.status_code != 200:
        # Register if needed
        requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Instructor", "email": "instructor@demo.com", "password": "password123", "role": "instructor"
        })
        resp = requests.post(f"{BASE_URL}/auth/login", json=inst_login)
    
    inst_token = resp.json()["access_token"]
    inst_headers = {"Authorization": f"Bearer {inst_token}"}
    
    # 2. Create a Draft Course
    course_data = {
        "title": "Visibility Test Course",
        "description": "This should be hidden",
        "thumbnail": "",
        "price": 0,
        "status": "Draft",
        "modules": []
    }
    resp = requests.post(f"{BASE_URL}/courses", json=course_data, headers=inst_headers)
    course_id = resp.json()["id"]
    log(f"Created Draft course with ID: {course_id}")
    
    # 3. Login as Learner
    learner_login = {"username": "learner@demo.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=learner_login)
    if resp.status_code != 200:
        requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Learner", "email": "learner@demo.com", "password": "password123", "role": "learner"
        })
        resp = requests.post(f"{BASE_URL}/auth/login", json=learner_login)
    
    learner_token = resp.json()["access_token"]
    learner_headers = {"Authorization": f"Bearer {learner_token}"}
    
    # Enroll learner in the course (even though it's draft, we want to see if it shows up in my-courses)
    requests.post(f"{BASE_URL}/courses/{course_id}/enroll", headers=learner_headers)
    
    # 4. Try to fetch as Learner via get_course
    resp = requests.get(f"{BASE_URL}/courses/{course_id}", headers=learner_headers)
    if resp.status_code == 403:
        log("SUCCESS: Learner correctly denied access to Draft course via detail endpoint.")
    else:
        log(f"FAILURE: Learner should have seen 403, but got {resp.status_code}")
        
    # 5. Try to fetch via my-courses
    resp = requests.get(f"{BASE_URL}/courses/my-courses", headers=learner_headers)
    my_courses = resp.json()
    found = any(c["id"] == course_id for c in my_courses)
    if not found:
        log("SUCCESS: Draft course correctly hidden from learner's My Courses list.")
    else:
        log("FAILURE: Draft course found in learner's My Courses list.")
        
    # 6. Cleanup - Delete as Instructor
    resp = requests.delete(f"{BASE_URL}/courses/{course_id}", headers=inst_headers)
    if resp.status_code == 200:
        log("SUCCESS: Instructor deleted the course.")
    else:
        log(f"FAILURE: Instructor could not delete course: {resp.status_code}")

if __name__ == "__main__":
    verify_visibility()
