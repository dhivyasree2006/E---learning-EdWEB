import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test():
    # 1. Login or Register
    email = f"tester_{int(time.time())}@example.com"
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Tester",
        "email": email,
        "password": "password",
        "role": "learner"
    })
    print(f"Register: {reg_res.status_code}")
    
    log_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": email,
        "password": "password"
    })
    print(f"Login: {log_res.status_code}")
    token = log_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Enroll
    requests.post(f"{BASE_URL}/courses/1/enroll", headers=headers)
    
    # 3. Submit Quiz
    payload = {"score": 100, "total_questions": 1}
    # Getting module id from course 1
    c_res = requests.get(f"{BASE_URL}/courses/1")
    mod_id = c_res.json()["modules"][0]["id"]
    print(f"Submitting for module {mod_id}...")
    
    sub_res = requests.post(f"{BASE_URL}/modules/{mod_id}/quiz/submit", json=payload, headers=headers)
    print(f"Submit Status: {sub_res.status_code}")
    print(f"Submit Response: {sub_res.text}")
    
    # 4. Check Progress
    my_res = requests.get(f"{BASE_URL}/courses/my-courses", headers=headers)
    print(f"My Progress: {my_res.json()[0]['progress']}%")

if __name__ == "__main__":
    test()
