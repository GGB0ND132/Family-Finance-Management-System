"""最终验证：交易流水和余额。"""
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

time.sleep(2)

# Test transactions
print("=== 验证流水 ===")
req = urllib.request.Request(
    f"{BASE}/transactions?family_id=1&scope=family",
    headers=AUTH,
    method="GET",
)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    txs = data["data"]["items"]
    print(f"  流水数: {len(txs)}")
    for t in txs:
        print(f"    {t['type']} {t['amount']} - {t['remark']}")
except urllib.error.HTTPError as e:
    print(f"  Error {e.code}: {e.read().decode()[:500]}")

# Test balance
print("\n=== 验证余额 ===")
req = urllib.request.Request(
    f"{BASE}/accounts?family_id=1",
    headers=AUTH,
    method="GET",
)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    for a in data["data"]["items"]:
        print(f"  账户 {a['name']}: 余额 = {a['current_balance']}")
    print(f"  期望余额: 2785.00")
except urllib.error.HTTPError as e:
    print(f"  Error {e.code}: {e.read().decode()[:500]}")

# Test with clean CSV (no duplicates)
print("\n=== 创建新批次验证导入 ===")
import uuid
csv_content = "交易时间,金额,收/支,分类,备注\n2026-09-08 10:00,50.00,支出,餐饮,午餐\n"
boundary = str(uuid.uuid4())
parts = []
for name, val in [
    ("family_id", "1"),
    ("account_id", "1"),
    ("scope", "personal"),
    ("field_mapping_json", json.dumps({
        "occurred_at": "交易时间",
        "amount": "金额",
        "direction": "收/支",
        "category": "分类",
        "remark": "备注",
    })),
]:
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode())
parts.append(csv_content.encode())
parts.append(f'\r\n--{boundary}--\r\n'.encode())
body = b"".join(parts)

req = urllib.request.Request(
    f"{BASE}/imports/preview",
    data=body,
    headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
batch_id = resp["data"]["batch_id"]
print(f"  预览: valid={resp['data']['valid_rows']}, batch_id={batch_id}")

req = urllib.request.Request(
    f"{BASE}/imports/{batch_id}/confirm",
    headers={**AUTH, "Content-Type": "application/json"},
    method="POST",
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print(f"  确认: imported_rows={resp['data']['imported_rows']}, status={resp['data']['status']}")

# Final balance
req = urllib.request.Request(
    f"{BASE}/accounts?family_id=1",
    headers=AUTH,
    method="GET",
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
for a in resp["data"]["items"]:
    print(f"  最终余额: {a['name']} = {a['current_balance']}")

print("\n=== 验证完成 ===")