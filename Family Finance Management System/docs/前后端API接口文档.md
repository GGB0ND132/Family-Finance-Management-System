# 家庭收支管理系统前后端 API 接口文档

**版本：** v1.0  
**基础路径：** `/api/v1`  
**说明：** 本文档是前后端联调契约；后端以 FastAPI/OpenAPI 为最终实现来源，字段调整必须先更新本文档。

## 1. 通用协议

### 1.1 请求头

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
X-Request-ID: <可选，建议由前端生成>
```

文件上传使用 `multipart/form-data`；导出请求使用 `Accept: text/csv` 或 Blob 响应。所有受保护接口缺少或无效 Token 返回 `401`。

### 1.2 成功响应

普通 JSON 接口统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "01JABC..."
}
```

创建资源返回 `201`；查询和更新返回 `200`；删除返回 `204` 且无响应体。列表 `data` 统一为：

```json
{"items": [], "page": 1, "page_size": 20, "total": 0}
```

### 1.3 错误响应

```json
{
  "code": 40001,
  "message": "金额必须大于0",
  "data": null,
  "request_id": "01JABC..."
}
```

状态码约定：`400` 业务参数错误，`401` 未登录，`403` 无权限，`404` 资源不存在，`409` 唯一性/余额/并发冲突，`422` 请求结构校验错误，`500` 未预期错误。422 的 `data` 示例：

```json
{"fields": [{"field": "amount", "reason": "必须大于0"}]}
```

前端统一拦截器：401 清理登录态；403 显示权限提示；409 显示业务冲突；422 映射表单字段；500 显示通用错误并保留 `request_id` 供排查。

### 1.4 字段与查询规则

- 金额字段：建议 JSON 传输字符串，如 `"amount": "12.30"`、`"current_balance": "100.00"`。
- 时间字段：ISO 8601，精确到分钟，如 `2026-09-06T13:42:00+08:00`。
- `family_id`：GET 放查询参数；POST/PUT/PATCH 放请求体；导入放 FormData；详情/DELETE 可省略，由后端反查。
- `scope`：仅 `personal` 或 `family`。个人接口由 JWT 反查当前成员，不能依赖前端传入任意 `member_id`。
- 分页：`page>=1`、`1<=page_size<=100`，默认 `page=1&page_size=20`。

## 2. 认证与用户

### POST `/auth/register`

请求：

```json
{"username": "alice", "password": "Passw0rd!", "nickname": "Alice"}
```

成功 `201`：`data` 为 `{ "id": 1, "username": "alice", "nickname": "Alice", "created_at": "..." }`；用户名重复返回 `409`。

### POST `/auth/login`

请求：

```json
{"username": "alice", "password": "Passw0rd!"}
```

成功 `200`：

```json
{"code":0,"message":"success","data":{"access_token":"eyJ...","token_type":"bearer","user":{"id":1,"username":"alice","nickname":"Alice"}},"request_id":"..."}
```

密码错误统一返回 `401` 和“用户名或密码错误”。

### GET `/users/me`

无请求体，返回当前用户基础信息。

### PATCH `/users/me`

请求 `{"nickname":"新昵称"}`，返回更新后的用户。

### PATCH `/users/me/password`

请求 `{"old_password":"旧密码","new_password":"NewPassw0rd!"}`；旧密码错误返回 `400`。

## 3. 家庭与成员

### GET `/families`

返回当前用户所属家庭列表：

```json
{"items":[{"id":10,"name":"我的家庭","role":"ADMIN","joined_at":"..."}],"page":1,"page_size":20,"total":1}
```

### POST `/families`

请求 `{"name":"我的家庭"}`。后端同事务创建家庭和管理员成员记录，并初始化默认分类。

### POST `/families/join`

请求 `{"invite_code":"ABCD1234"}`。邀请码无效、过期或重复加入返回 `409`。

### PATCH `/families/{family_id}`

请求 `{"name":"新家庭名称"}`，仅管理员。

### GET `/families/{family_id}/members`

返回成员列表：`id、user_id、username、nickname、role、joined_at`。

### POST `/families/{family_id}/invite-code` / DELETE `/families/{family_id}/invite-code`

生成或失效邀请码，仅管理员。生成成功返回 `invite_code、invite_expires_at`。

### PATCH/DELETE `/families/{family_id}/members/{member_id}`

PATCH 请求 `{"role":"ADMIN"}` 或 `{"role":"MEMBER"}`；删除/降权最后管理员返回 `409`。

## 4. 账户与分类

### GET `/accounts?family_id={id}&scope=personal|family&owner_member_id={id}`

返回账户分页。个人范围由后端强制当前成员过滤；销户账户可在历史查询中返回，但不得进入新增流水候选。

### POST `/accounts`

请求：

```json
{"family_id":10,"owner_member_id":3,"name":"招商银行","type":"BANK_CARD","initial_balance":"1000.00","remark":"工资卡"}
```

成功返回账户及 `current_balance`（初始时等于 `initial_balance`）。

### PATCH `/accounts/{id}` / DELETE `/accounts/{id}`

PATCH 可更新名称、类型、所属人和备注。DELETE 时余额非零返回 `409`；无历史引用物理删除，有流水/转账引用则写入 `closed_at`。

### GET `/categories?family_id={id}&type=INCOME|EXPENSE`

返回可用或历史分类。

### POST `/categories`

请求 `{"family_id":10,"name":"兼职","type":"INCOME","icon":"work","color":"#4E9F6E"}`；同家庭同方向重名返回 `409`。

### PATCH/DELETE `/categories/{id}`

已被流水或预算引用的分类执行软删除，历史记录保留原名称。

## 5. 收支流水

### GET `/transactions`

查询参数：`family_id、scope、page、page_size、from、to、type、account_id、owner_member_id、category_id、beneficiary_member_id、recorder_user_id、min_amount、max_amount`。时间边界为分钟；个人范围按资金归属人过滤。

### POST `/transactions`

请求：

```json
{"family_id":10,"account_id":21,"category_id":31,"beneficiary_member_id":3,"type":"EXPENSE","amount":"35.60","occurred_at":"2026-09-06T13:42:00+08:00","remark":"午餐"}
```

`recorder_user_id` 由后端从 JWT 写入，前端不得伪造。后端校验账户/分类/成员同家庭、账户未销户、分类方向匹配和金额大于 0。成功返回流水详情及最新账户余额。

### GET/PATCH/DELETE `/transactions/{id}`

PATCH 可修改金额、账户、分类、资金归属人、发生时间和备注；服务端先撤销旧余额影响，再应用新影响，同事务提交。DELETE 反向恢复余额。普通成员仅能维护账户所属人为自己、资金归属人为自己或自己录入的流水。

## 6. 家庭内部转账

### GET `/transfers?family_id={id}&scope=personal|family&page=1&page_size=20&from=...&to=...`

个人范围只返回当前成员作为转出方或转入方的记录。

### POST `/transfers`

请求：

```json
{"family_id":10,"from_account_id":21,"to_account_id":22,"amount":"200.00","occurred_at":"2026-09-06T14:00:00+08:00","remark":"生活费"}
```

后端自动带出双方成员和录入人；两个账户必须同家庭、未销户且不同。按账户 ID 顺序加锁，转出减余额、转入加余额、写入 transfers，任一步失败全部回滚。

### PATCH/DELETE `/transfers/{id}`

编辑先恢复原转账，再应用新转账；删除反向恢复两个账户余额。转账不生成 transactions，不进入收入、支出、结余和预算。

## 7. 报表与预算

### 个人报表

- `GET /reports/personal/daily?family_id={id}&date=YYYY-MM-DD`
- `GET /reports/personal/summary?family_id={id}&from=...&to=...`
- `GET /reports/personal/trend?family_id={id}&from=YYYY-MM&to=YYYY-MM`
- `GET /reports/personal/by-category?family_id={id}&month=YYYY-MM`

个人收入/支出按 `beneficiary_member_id` 聚合，返回个人资产、趋势、分类占比和转账/资产变动，不返回成员对比。

### 家庭报表

- `GET /reports/family/summary?family_id={id}&month=YYYY-MM`
- `GET /reports/family/trend?family_id={id}&from=YYYY-MM&to=YYYY-MM`
- `GET /reports/family/by-category?family_id={id}&month=YYYY-MM`
- `GET /reports/family/by-member?family_id={id}&month=YYYY-MM`

家庭收入/支出按当前家庭全部流水聚合；转账单独展示，不能污染收支、结余和预算。无数据返回零值指标和空数组。

### GET/PUT `/budgets/{month}?family_id={id}&scope=personal|family`

PUT 请求示例：

```json
{"family_id":10,"scope":"personal","total_amount":"3000.00","categories":[{"category_id":31,"amount":"1200.00"},{"category_id":32,"amount":"800.00"}]}
```

响应返回 `total_amount、used_amount、remaining_amount、usage_rate、warning_level、categories[]`。个人预算仅本人保存，家庭预算仅管理员保存；预算仅统计支出。

### POST `/budgets/{month}/copy-from-previous`

请求 `{"family_id":10,"scope":"family"}`，只复制同范围上月预算草稿。

## 8. 导入与导出

### POST `/imports/preview`

`multipart/form-data` 字段：`file、family_id、account_id、scope、field_mapping_json`。成功返回批次摘要和预览行：

```json
{"batch_id":1001,"status":"PREVIEWED","total_rows":3,"valid_rows":2,"invalid_rows":0,"duplicate_rows":1,"rows":[{"row_number":2,"validation_status":"VALID","normalized_data":{}}]}
```

重复键为“账户 + 分钟级时间 + 两位小数金额 + 去首尾空白备注”；重复行默认跳过。文件只有日期时补 `00:00` 并提示。

### GET `/imports/{id}` / POST `/imports/{id}/confirm`

仅上传人或管理员可访问。确认时再次校验家庭、账户、分类、成员和销户状态；有效行批量写入和余额更新必须整体事务提交，失败则批次 `FAILED` 并全部回滚。

### GET `/exports/transactions`

查询参数：`family_id、scope、from、to、format=csv|xlsx` 及流水筛选字段。CSV 返回 `text/csv; charset=utf-8`（含 UTF-8 BOM）；XLSX 返回 Blob，前端使用 `responseType: 'blob'`。响应头：

```http
Content-Disposition: attachment; filename*=UTF-8''transactions-2026-09.xlsx
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

导出列至少为：发生时间、类型、金额、账户、账户所属人、分类、资金归属人、录入人、备注、创建时间。错误下载响应仍为统一错误 JSON，前端需先读取 Blob 文本再提示。

## 9. 联调示例

```ts
const res = await apiClient.get<ApiResponse<Page<Transaction>>>('/transactions', {
  params: { family_id: currentFamilyId, scope: 'personal', page: 1, page_size: 20 }
});
const page = res.data.data;
```

```ts
try {
  await apiClient.post('/transactions', payload);
} catch (e) {
  // 拦截器将 422 fields 映射到 Form；409/403 显示 message；401 跳转登录
}
```

联调完成标准：前端类型与 OpenAPI 一致；每个接口至少验证成功、401、403、404/409、422 和网络错误；金额、时间、分页及 Blob 下载在桌面和移动端均可复现。
