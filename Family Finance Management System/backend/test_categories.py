"""测试分类接口修复。"""
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

# Wait for reload
time.sleep(2)

# Test categories endpoint
print("Testing categories endpoint...")
req = urllib.request.Request(
    f"{BASE}/categories?family_id=1",
    headers=AUTH,
    method="GET",
)
try:
    resp = urllib.request.urlopen(req)
    body = json.loads(resp.read().decode())
    print(f"Categories: {resp.status} OK")
    for c in body["data"]["items"]:
        print(f"  {c['name']} ({c['type']}) id={c['id']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:500]}")