import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(msg)

def test_rag_chat():
    # 1. Login as Learner
    log("Logging in as learner...")
    login_data = {"username": "learner@demo.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if resp.status_code != 200:
        # Try registering if not exists
        log("Login failed, trying to register...")
        requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Learner", "email": "learner@demo.com", "password": "password123", "role": "learner"
        })
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
    if resp.status_code != 200:
        log(f"Failed to login: {resp.text}")
        return

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test Chat Endpoint
    log("Testing /api/chat...")
    # First, let's ask something generic
    query = "What is this platform about?"
    resp = requests.post(f"{BASE_URL}/api/chat", json={"message": query}, headers=headers)
    
    if resp.status_code == 200:
        log("SUCCESS: Chat API responded.")
        log(f"Query: {query}")
        log(f"Response: {resp.json().get('response')}")
    else:
        log(f"FAILURE: Chat API returned {resp.status_code}")
        log(resp.text)

    # 3. Test RAG Context (if courses exist)
    # We assume 'Python' or some course exists from previous setup or the startup indexing
    query = "What do you have on Python?"
    resp = requests.post(f"{BASE_URL}/api/chat", json={"message": query}, headers=headers)
    
    if resp.status_code == 200:
        log("SUCCESS: Chat API responded (RAG Test).")
        log(f"Query: {query}")
        log(f"Response: {resp.json().get('response')}")
    else:
        log(f"FAILURE: Chat API returned {resp.status_code}")

if __name__ == "__main__":
    test_rag_chat()
