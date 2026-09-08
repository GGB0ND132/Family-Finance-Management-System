import json, uuid, urllib.request

BASE = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg4ODM1MTc2fQ.rcvWuDGU7fpoMV6HmH_Mm42w-MuWNqC71AHRGZM7cbI"

csv_content = open("test_bill.csv", encoding="utf-8").read()
boundary = str(uuid.uuid4())
parts = []
for name, val in [
    ("family_id", "1"),
    ("account_id", "2"),
    ("scope", "personal"),
    ("field_mapping_json", json.dumps({
        "occurred_at": "交易时间", "amount": "金额",
        "direction": "收/支", "category": "分类", "remark": "备注",
    })),
]:
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test_bill.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode())
parts.append(csv_content.encode())
parts.append(f'\r\n--{boundary}--\r\n'.encode())

req = urllib.request.Request(
    f"{BASE}/imports/preview", data=b"".join(parts),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST",
)
resp = json.loads(urllib.request.urlopen(req).read().decode())
print(json.dumps(resp, indent=2, ensure_ascii=False))