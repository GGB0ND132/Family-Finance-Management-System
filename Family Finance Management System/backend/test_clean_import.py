"""测试纯净 CSV 的完整导入流程。"""
import json
import urllib.request
import uuid

BASE = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg4ODMwODM1fQ.Nd0UY8WWtSfsDqAFGRNTt2mucNWoMeEiP3qRzBhA6uo"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def step(msg):
    print(f"\n=== {msg} ===")


# Upload clean CSV
step("上传纯净 CSV（3 行有效）")
csv_content = "交易时间,金额,收/支,分类,备注\n2026-09-06 13:42,128.50,支出,餐饮,晚餐\n2026-09-06 14:00,3000.00,收入,工资,九月工资\n2026-09-07 08:00,86.50,支出,餐饮,早餐\n"
with open("test_clean.csv", "w", encoding="utf-8") as f:
    f.write(csv_content)

boundary = str(uuid.uuid4())
parts = []
for name, val in [
    ("family_id", "1"),
    ("account_id", "1"),
    ("scope", "personal"),
    (
        "field_mapping_json",
        json.dumps(
            {
                "occurred_at": "交易时间",
                "amount": "金额",
                "direction": "收/支",
                "category": "分类",
                "remark": "备注",
            }
        ),
    ),
]:
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode()
    )
parts.append(
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test_clean.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode()
)
parts.append(csv_content.encode())
parts.append(f"\r\n--{boundary}--\r\n".encode())
body = b"".join(parts)

req = urllib.request.Request(
    f"{BASE}/imports/preview",
    data=body,
    headers={**AUTH, "Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
batch_id = resp["data"]["batch_id"]
print(f'  预览: valid={resp["data"]["valid_rows"]}, batch_id={batch_id}')

# Confirm
step("确认导入")
req = urllib.request.Request(
    f"{BASE}/imports/{batch_id}/confirm",
    headers={**AUTH, "Content-Type": "application/json"},
    method="POST",
)
try:
    resp = json.loads(urllib.request.urlopen(req).read().decode())
    print(f"  确认成功: imported_rows={resp['data']['imported_rows']}")
except urllib.error.HTTPError as e:
    print(f"  确认失败: {e.code} {e.read().decode()[:200]}")

# Check transactions
step("验证流水")
req = urllib.request.Request(
    f"{BASE}/transactions?family_id=1&scope=family", headers=AUTH, method="GET"
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
txs = resp["data"]["items"]
print(f"  流水数: {len(txs)}")
for tx in txs:
    print(f"    {tx['type']} {tx['amount']} - {tx['remark']}")

# Check balance
step("验证余额")
req = urllib.request.Request(
    f"{BASE}/accounts?family_id=1", headers=AUTH, method="GET"
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
for acc in resp["data"]["items"]:
    print(f"  账户 {acc['name']}: 余额 = {acc['current_balance']}")
print(f"  期望余额: 2785.00")