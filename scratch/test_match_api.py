import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/admin/match"
data = {
    "key": "withpro123",
    "id": 1,
    "pro_id": 1
}

payload = json.dumps(data).encode("utf-8")

def run_test(host_header):
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Host": host_header
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            print(f"[{host_header}] Success! Status: {response.status}")
            print("Response:", response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[{host_header}] HTTP Error {e.code}")
        print("Response Body:", e.read().decode("utf-8"))
    except Exception as e:
        print(f"[{host_header}] Other error:", e)

print("Running Test 1...")
run_test("withpro")

print("\nRunning Test 2...")
run_test("withpro.co.kr")
