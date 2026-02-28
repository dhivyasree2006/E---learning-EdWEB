import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GROQ_API_KEY")
print(f"Loaded Key: {key[:10]}...{key[-5:]}" if key else "Key not found")

if not key:
    print("Error: GROQ_API_KEY not found in environment.")
    exit(1)

try:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": "Hello, respond with 'Valid' if you can hear me."}
            ],
            "max_tokens": 5
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
