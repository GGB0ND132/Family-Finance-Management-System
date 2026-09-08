"""
验证：外部账单导入模块完整流程
使用已有数据继续验证
"""
import json
import urllib.request
import uuid
import os

BASE = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


def _req(method, path, body=None, headers=None):
    h = HEADERS.copy()
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


# ========== 0. 登录 ==========
step("0. 登录已有用户")
status, data = _req("POST", "/auth/login", {"username": "alice", "password": "password123"})
assert status == 200, f"登录失败: {data}"
TOKEN = data["data"]["access_token"]
AUTH = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
print(f"  Token: {TOKEN[:30]}...")

# ========== 1. 获取家庭 ==========
step("1. 获取家庭列表")
status, data = _req("GET", "/families", headers=AUTH)
print(f"  GET /families → {status}")
assert status == 200 and data["data"], f"无家庭数据: {data}"
family_id = data["data"][0]["id"]
print(f"  family_id = {family_id}")

# ========== 2. 获取成员 ==========
step("2. 获取成员")
status, data = _req("GET", f"/families/{family_id}/members", headers=AUTH)
assert status == 200 and data["data"], f"无成员数据: {data}"
member_id = data["data"][0]["id"]
print(f"  member_id = {member_id}")

# ========== 3. 获取分类 ==========
step("3. 获取已有分类")
status, data = _req("GET", f"/categories?family_id={family_id}", headers=AUTH)
print(f"  GET /categories → {status}")
cats = {c["name"]: c["id"] for c in data["data"]["items"]}
print(f"  已有分类: {list(cats.keys())}")

# 创建缺少的分类
if "餐饮" not in cats:
    status, data = _req("POST", "/categories", {"family_id": family_id, "name": "餐饮", "type": "EXPENSE"}, headers=AUTH)
    print(f"  创建分类「餐饮」→ {status}")
    cats["餐饮"] = data["data"]["id"]

if "工资" not in cats:
    status, data = _req("POST", "/categories", {"family_id": family_id, "name": "工资", "type": "INCOME"}, headers=AUTH)
    print(f"  创建分类「工资」→ {status}")
    cats["工资"] = data["data"]["id"]

print(f"  最终分类: {cats}")

# ========== 4. 创建账户 ==========
step("4. 创建账户（余额 0）")
# 先检查已有账户
status, data = _req("GET", f"/accounts?family_id={family_id}", headers=AUTH)
account_id = None
if status == 200 and data["data"]["items"]:
    for acc in data["data"]["items"]:
        if acc["name"] == "钱包":
            account_id = acc["id"]
            print(f"  已有账户「钱包」id={account_id}, 余额={acc['current_balance']}")
            break

if not account_id:
    status, data = _req("POST", "/accounts", {
        "family_id": family_id,
        "owner_member_id": member_id,
        "name": "钱包",
        "type": "CASH",
        "initial_balance": "0.00",
        "remark": "测试用",
    }, headers=AUTH)
    print(f"  POST /accounts → {status}")
    account_id = data["data"]["id"]
    print(f"  创建账户「钱包」id={account_id}")

# ========== 5. 准备测试 CSV ==========
step("5. 准备测试 CSV 文件")
csv_content = "交易时间,金额,收/支,分类,备注\n2026-09-06 13:42,128.50,支出,餐饮,晚餐\n2026-09-06 14:00,3000.00,收入,工资,九月工资\n2026-09-06 15:00,abc,支出,餐饮,金额错误行\n2026-09-07 08:00,86.50,支出,餐饮,早餐\n"
csv_path = "test_bill.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write(csv_content)
print(f"  CSV 文件已创建: {csv_path}")
print(f"  4 行数据：3 有效行 + 1 非法行（金额 abc）")

# ========== 6. 上传预览 ==========
step("6. 上传预览 (POST /imports/preview)")
boundary = str(uuid.uuid4())
body_parts = []

def add_field(name, value):
    body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())

add_field("family_id", str(family_id))
add_field("account_id", str(account_id))
add_field("scope", "personal")
add_field("field_mapping_json", json.dumps({
    "occurred_at": "交易时间",
    "amount": "金额",
    "direction": "收/支",
    "category": "分类",
    "remark": "备注",
}))

file_data = csv_content.encode("utf-8")
body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="test_bill.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode())
body_parts.append(file_data)
body_parts.append(f'\r\n--{boundary}--\r\n'.encode())

body = b"".join(body_parts)
content_type = f"multipart/form-data; boundary={boundary}"

req = urllib.request.Request(
    f"{BASE}/imports/preview",
    data=body,
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": content_type},
    method="POST",
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f"  POST /imports/preview → {resp.status}")
    batch_id = result["data"]["batch_id"]
    print(f"  batch_id = {batch_id}")
    print(f"  status = {result['data']['status']}")
    print(f"  total_rows = {result['data']['total_rows']}")
    print(f"  valid_rows = {result['data']['valid_rows']}")
    print(f"  invalid_rows = {result['data']['invalid_rows']}")
    print(f"  duplicate_rows = {result['data']['duplicate_rows']}")
    for row in result["data"]["rows"]:
        print(f"    行 {row['row_number']}: {row['validation_status']}  errors={row['errors']}")
except urllib.error.HTTPError as e:
    print(f"  ERROR {e.code}: {e.read().decode()}")
    raise

# ========== 7. 查询批次详情 ==========
step("7. 查询批次详情")
status, data = _req("GET", f"/imports/{batch_id}", headers=AUTH)
print(f"  GET /imports/{batch_id} → {status}")
print(f"  status = {data['data']['status']}")
print(f"  valid_rows = {data['data']['valid_rows']}")

# ========== 8. 确认导入 ==========
step("8. 确认导入 (POST /imports/{batch_id}/confirm)")
status, data = _req("POST", f"/imports/{batch_id}/confirm", headers=AUTH)
print(f"  POST /imports/{batch_id}/confirm → {status}")
if status == 200:
    print(f"  imported_rows = {data['data']['imported_rows']}")
    print(f"  status = {data['data']['status']}")
else:
    print(f"  ERROR: {data}")

# ========== 9. 验证流水和余额 ==========
step("9. 验证结果")
status, data = _req("GET", f"/transactions?family_id={family_id}&scope=family", headers=AUTH)
print(f"  GET /transactions?family_id={family_id}&scope=family → {status}")
if status == 200:
    txs = data["data"]["items"]
    print(f"  流水数 = {len(txs)}")
    for tx in txs:
        print(f"    {tx['type']} {tx['amount']} - {tx['remark']}")

status, data = _req("GET", f"/accounts?family_id={family_id}", headers=AUTH)
print(f"\n  GET /accounts?family_id={family_id} → {status}")
if status == 200:
    for acc in data["data"]["items"]:
        print(f"    账户 {acc['name']}: 余额 = {acc['current_balance']}")
    # 期望余额 = 0 + 3000(收入) - 128.50(支出) - 86.50(支出) = 2785.00
    print(f"    期望余额: 2785.00")

# ========== 10. 重复确认拦截 ==========
step("10. 重复确认拦截")
status, data = _req("POST", f"/imports/{batch_id}/confirm", headers=AUTH)
print(f"  POST /imports/{batch_id}/confirm (重复) → {status}")
if status == 400:
    print(f"  正确拦截: {data['message']}")

# ========== 11. 越权验证 ==========
step("11. 越权验证（无效 Token）")
status, data = _req("GET", f"/imports/{batch_id}", headers={"Authorization": "Bearer fake-token"})
print(f"  GET /imports/{batch_id} (无效 Token) → {status}")

print(f"\n{'='*60}")
print(f"  验证完成！")
print(f"{'='*60}")