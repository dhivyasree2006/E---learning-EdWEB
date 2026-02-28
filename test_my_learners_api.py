import requests

def test_my_learners():
    # First login as instructor
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {"username": "instructor@edweb.com", "password": "password123"}
    login_res = requests.post(login_url, json=login_data)
    token = login_res.json()["access_token"]
    
    # Then get learners
    url = "http://127.0.0.1:8000/courses/my-learners"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    try:
        print(f"Learners: {response.json()}")
    except:
        print(f"Response (text): {response.text}")

if __name__ == "__main__":
    test_my_learners()
