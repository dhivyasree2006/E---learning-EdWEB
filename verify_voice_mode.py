import requests
import json

def test_clean_speech():
    url = "http://127.0.0.1:8000/api/ai/clean-speech"
    
    test_cases = [
        "I... I want to... select... option A",
        "The first... first option please",
        "Wh-what is the... the answer for... gravity"
    ]
    
    print("Testing AI Speech Cleaning Endpoint...")
    
    for text in test_cases:
        print(f"\nRaw: {text}")
        try:
            response = requests.post(url, json={"text": text})
            if response.status_code == 200:
                cleaned = response.json().get("cleaned_text")
                print(f"Cleaned: {cleaned}")
            else:
                print(f"Error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_clean_speech()
