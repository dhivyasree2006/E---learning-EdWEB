import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_ai_generation_mcq():
    print("Testing MCQ generation...")
    # We need a token. We can use the test_login logic if needed.
    # But for a quick check, let's assume the server is running and we can login.
    
    # Login as instructor
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "instructor@edweb.com",
        "password": "password123"
    })
    
    if login_res.status_code != 200:
        print("Login failed. Make sure server is running and instructor@gmail.com exists.")
        return

    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test MCQ
    res = requests.post(f"{BASE_URL}/api/ai/generate-questions", headers=headers, json={
        "topic": "React Hooks",
        "questionType": "mcq",
        "count": 3
    })
    
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        questions = res.json()["questions"]
        print(f"Generated {len(questions)} questions.")
        print(json.dumps(questions[0], indent=2))
        assert len(questions) > 0
        assert "questionText" in questions[0]
        assert "options" in questions[0]
        assert len(questions[0]["options"]) == 4
    else:
        print(res.text)

def test_ai_generation_descriptive():
    print("\nTesting Descriptive generation...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "instructor@edweb.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = requests.post(f"{BASE_URL}/api/ai/generate-questions", headers=headers, json={
        "topic": "Async Programming",
        "questionType": "descriptive",
        "count": 2
    })
    
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        questions = res.json()["questions"]
        print(f"Generated {len(questions)} questions.")
        print(json.dumps(questions[0], indent=2))
        assert len(questions) > 0
        assert "questionText" in questions[0]
        assert "correctAnswerText" in questions[0]
    else:
        print(res.text)

if __name__ == "__main__":
    try:
        test_ai_generation_mcq()
        test_ai_generation_descriptive()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
