import requests

def test_learner_dashboard():
    # First login as learner
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {"username": "miru@gmail.com", "password": "password123"}
    login_res = requests.post(login_url, json=login_data)
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test my-courses
    my_courses_res = requests.get("http://127.0.0.1:8000/courses/my-courses", headers=headers)
    print(f"My Courses Status: {my_courses_res.status_code}")
    print(f"My Courses: {my_courses_res.json()}")
    
    # Test all courses
    all_courses_res = requests.get("http://127.0.0.1:8000/courses", headers=headers)
    print(f"All Courses Status: {all_courses_res.status_code}")
    print(f"All Courses Count: {len(all_courses_res.json())}")

if __name__ == "__main__":
    test_learner_dashboard()
