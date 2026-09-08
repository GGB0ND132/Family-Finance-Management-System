"""Debug categories endpoint."""
import json
import urllib.request
import time

BASE = "http://localhost:8000/api/v1"

# Login
req = urllib.request.Request(
    f"{BASE}/auth/login",
    data=json.dumps({"username": "alice", "password": "password123"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
token = d["data"]["access_token"]
AUTH = {"Authorization": f"Bearer {token}"}

time.sleep(1)

# Test categories
print("Testing GET /categories?family_id=1 ...")
req = urllib.request.Request(
    f"{BASE}/categories?family_id=1",
    headers=AUTH,
    method="GET",
)
try:
    resp = urllib.request.urlopen(req)
    body = json.loads(resp.read().decode())
    print(f"OK: {resp.status}")
    print(f"Items: {len(body['data']['items'])}")
    for c in body['data']['items']:
        print(f"  id={c['id']} name={c['name']} type={c['type']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"ERROR: {e.code}")
    print(f"Body: {body}")