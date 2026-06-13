import urllib.request
import json
import sys

# Reconfigure stdout to use utf-8 to prevent encoding errors on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test_homepage():
    try:
        response = urllib.request.urlopen("http://localhost:8000/index.html")
        status = response.getcode()
        html = response.read().decode('utf-8')
        if status == 200 and "withPRO" in html:
            print("SUCCESS: Homepage loaded correctly.")
        else:
            print(f"FAILURE: Homepage status {status}, html content check failed.")
    except Exception as e:
        print(f"ERROR testing homepage: {e}")

def test_request_lesson():
    try:
        data = {
            "userName": "테스트유저",
            "userContact": "010-9999-8888",
            "golfCourse": "테스트 CC",
            "date": "2026-06-20",
            "time": "09:00",
            "user_id": "TEST_USER_99"
        }
        req_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8000/api/request-lesson",
            data=req_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            res_content = response.read().decode('utf-8')
            res_data = json.loads(res_content)
            # Remove high-unicode characters from output to be safe on printing
            safe_message = res_data.get('message', '').replace('⛳', '[GOLF]')
            print("Response status:", res_data.get('status'))
            print("Response message (safe):", safe_message)
            if res_data.get('status') == 'success' and 'id' in res_data:
                print("SUCCESS: Lesson request API works.")
                return res_data['id']
            else:
                print("FAILURE: Request lesson response invalid.")
    except Exception as e:
        print(f"ERROR testing request lesson API: {e}")
    return None

if __name__ == '__main__':
    print("Starting API tests against local server...")
    test_homepage()
    lesson_id = test_request_lesson()
    if lesson_id:
        print(f"Created lesson ID: {lesson_id}")
