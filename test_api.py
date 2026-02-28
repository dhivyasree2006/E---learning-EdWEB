import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_registration_and_login():
    # 0. Check public courses
    print("Checking public courses...")
    public_res = requests.get(f"{BASE_URL}/courses")
    print(f"Public courses status: {public_res.status_code}")
    if public_res.status_code == 200:
        print(f"Public courses count: {len(public_res.json())}")
    else:
        print(f"Public courses failed: {public_res.text}")

    # 1. Register a new user
    email = f"test_{int(time.time())}@example.com"
    payload = {
        "email": email,
        "name": "Test User",
        "password": "password123",
        "role": "learner"
    }
    
    print(f"Registering user: {email}...")
    register_response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Register status: {register_response.status_code}")
    print(f"Register body: {register_response.json()}")
    
    if register_response.status_code != 200:
        print("Registration failed!")
        return

    # 2. Login
    login_payload = {
        "username": email,
        "password": "password123"
    }
    print(f"Logging in user: {email}...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        print(f"Login successful! Token: {login_data['access_token'][:20]}...")
        token = login_data['access_token']
        
        # 3. Verify get current courses
        headers = {"Authorization": f"Bearer {token}"}
        # 5. Get My Courses (expected empty)
        my_res = requests.get(f"{BASE_URL}/courses/my-courses", headers=headers)
        print(f"My Courses status: {my_res.status_code}")
        my_courses = my_res.json()
        print(f"My Courses count: {len(my_courses)}")

        # 6. Enroll in a course (id 1)
        print("Enrolling in course 1...")
        enroll_res = requests.post(f"{BASE_URL}/courses/1/enroll", headers=headers)
        print(f"Enroll status: {enroll_res.status_code}")

        # 7. Check My Courses again (expected 1)
        my_res = requests.get(f"{BASE_URL}/courses/my-courses", headers=headers)
        my_courses = my_res.json()
        print(f"My Courses count (after enroll): {len(my_courses)}")
        if len(my_courses) > 0:
            print(f"Progress: {my_courses[0].get('progress')}%")

        # 8. Submit a quiz result for module 1
        print("Submitting quiz result for module 1...")
        # Need to find module id for course 1
        course_1_res = requests.get(f"{BASE_URL}/courses/1")
        course_1 = course_1_res.json()
        if course_1.get('modules'):
            module_id = course_1['modules'][0]['id']
            quiz_payload = {
                "score": 100,
                "total_questions": 1
            }
            quiz_res = requests.post(f"{BASE_URL}/modules/{module_id}/quiz/submit", json=quiz_payload, headers=headers)
            print(f"Quiz submit status: {quiz_res.status_code}")

        # 9. Verify progress updated
        my_res = requests.get(f"{BASE_URL}/courses/my-courses", headers=headers)
        my_courses = my_res.json()
        if len(my_courses) > 0:
            print(f"New Progress: {my_courses[0].get('progress')}%")

        # 10. Test Instructor Reports
        print("\nTesting Instructor Reports...")
        inst_login = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "instructor@edweb.com",
            "password": "password123"
        })
        if inst_login.status_code == 200:
            inst_headers = {"Authorization": f"Bearer {inst_login.json()['access_token']}"}
            learners_res = requests.get(f"{BASE_URL}/courses/my-learners", headers=inst_headers)
            print(f"My Learners status: {learners_res.status_code}")
            if learners_res.status_code == 200:
                learners = learners_res.json()
                print(f"Report count: {len(learners)}")
                if len(learners) > 0:
                    print(f"First learner progress: {learners[0].get('progress')}%")
            else:
                print(f"Learnres report failed: {learners_res.text}")
        else:
            print("Instructor login failed (make sure seed.py was run)")

    else:
        print(f"Login failed: {login_response.text}")

if __name__ == "__main__":
    test_registration_and_login()
