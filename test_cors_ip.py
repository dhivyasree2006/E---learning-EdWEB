import requests

BASE_URL = "http://127.0.0.1:8000"
ORIGIN = "http://127.0.0.1:5173"

def log(msg):
    print(msg)
    with open("cors_test_ip_result.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_cors():
    with open("cors_test_ip_result.log", "w", encoding="utf-8") as f:
        f.write("Running CORS test for IP...\n")

    log(f"Testing CORS for origin: {ORIGIN}")
    
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "GET",
    }
    
    try:
        response = requests.options(f"{BASE_URL}/courses/my-courses", headers=headers)
        log(f"Status Code: {response.status_code}")
        log("Headers:")
        for k, v in response.headers.items():
            if "access-control" in k.lower():
                log(f"{k}: {v}")
        
        if response.status_code == 200 and "access-control-allow-origin" in response.headers:
             log("CORS Preflight Check Passed!")
        else:
             log("CORS Preflight Check FAILED.")

    except Exception as e:
        log(f"Error: {e}")

if __name__ == "__main__":
    test_cors()
