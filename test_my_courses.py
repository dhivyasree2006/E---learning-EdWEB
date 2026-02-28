import requests

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(msg)
    with open("test_result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_my_courses():
    # Clear log
    with open("test_result.log", "w", encoding="utf-8") as f:
        f.write("Running test_my_courses...\n")

    # 1. Login
    login_data = {
        "username": "learner@demo.com",
        "password": "password123"
    }
    
    log(f"Logging in as {login_data['username']}...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            log(f"Login failed: {response.status_code} - {response.text}")
            # Try registering if login fails
            log("Trying to register...")
            reg_data = {
                "name": "Demo Learner",
                "email": "learner@demo.com",
                "password": "password123",
                "role": "learner"
            }
            reg_resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
            if reg_resp.status_code == 200:
                log("Registered successfully. Logging in again...")
                response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            else:
                log(f"Registration failed: {reg_resp.status_code} - {reg_resp.text}")
                return

        token = response.json()["access_token"]
        log("Login successful.")
        
        # 2. Get My Courses
        headers = {"Authorization": f"Bearer {token}"}
        log("Fetching my courses...")
        resp = requests.get(f"{BASE_URL}/courses/my-courses", headers=headers)
        
        if resp.status_code == 200:
            courses = resp.json()
            log(f"Success! Found {len(courses)} courses.")
            for c in courses:
                log(f"- {c['title']} (Progress: {c.get('progress')}%)")
        else:
            log(f"Failed to fetch courses: {resp.status_code} - {resp.text}")

    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    test_my_courses()
