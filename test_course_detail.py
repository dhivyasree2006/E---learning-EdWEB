import requests

BASE_URL = "http://127.0.0.1:8000"
COURSE_ID = 2
ORIGIN = "http://127.0.0.1:5173"

def log(msg):
    print(msg)
    with open("course_test_result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_course_detail():
    with open("course_test_result.log", "w", encoding="utf-8") as f:
        f.write("Running Course Detail Test...\n")

    # 1. Test OPTIONS (Preflight)
    log(f"Testing OPTIONS for /courses/{COURSE_ID}")
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization"
    }
    try:
        resp = requests.options(f"{BASE_URL}/courses/{COURSE_ID}", headers=headers)
        log(f"OPTIONS Status: {resp.status_code}")
        if "access-control-allow-origin" in resp.headers:
             log(f"CORS Header Present: {resp.headers['access-control-allow-origin']}")
        else:
             log("CORS Header MISSING in OPTIONS response")
    except Exception as e:
        log(f"OPTIONS Failed: {e}")

    # 2. Test GET (Actual Request) - We need a token? 
    # The endpoint get_course depends on get_db but NOT get_current_user in the definition I saw?
    # Let's check main.py line 393: 
    # @app.get("/courses/{course_id}")
    # def get_course(course_id: int, db: Session = Depends(database.get_db)):
    # It does NOT verify auth! So we can request it without token.
    
    log(f"Testing GET for /courses/{COURSE_ID}")
    headers = {
        "Origin": ORIGIN
    }
    try:
        resp = requests.get(f"{BASE_URL}/courses/{COURSE_ID}", headers=headers)
        log(f"GET Status: {resp.status_code}")
        log(f"Response: {resp.text[:500]}") # First 500 chars
        
        if "access-control-allow-origin" in resp.headers:
             log(f"CORS Header Present: {resp.headers['access-control-allow-origin']}")
        else:
             log("CORS Header MISSING in GET response")
             
    except Exception as e:
        log(f"GET Failed: {e}")

if __name__ == "__main__":
    test_course_detail()
