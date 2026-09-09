# 后端部署说明

后端是基于 FastAPI 的家庭收支管理 API，要求 Python 3.11 或更高版本，并使用 MySQL 数据库。

## 1. 准备数据库和环境变量

创建 MySQL 数据库，并确保字符集为 `utf8mb4`。例如：

```sql
CREATE DATABASE family_finance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

在 `backend/` 目录执行：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，至少修改 `DATABASE_URL` 和 `JWT_SECRET_KEY`。连接串格式如下：

```text
mysql+pymysql://用户名:密码@主机:端口/family_finance?charset=utf8mb4
```

生产环境还应根据实际前端地址调整 `CORS_ORIGINS`。

## 2. 使用 UV 部署

先安装 [UV](https://docs.astral.sh/uv/)，然后在后端目录执行：

```powershell
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

开发调试时可使用热重载：

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

## 3. 不使用 UV 部署

使用 Python 自带的虚拟环境和 `pip`：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install alembic email-validator fastapi openpyxl "passlib[bcrypt]" pydantic-settings pymysql python-dotenv "python-jose[cryptography]" python-multipart sqlalchemy "uvicorn[standard]"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果 PowerShell 禁止执行激活脚本，可以改用命令提示符：

```bat
.venv\Scripts\activate.bat
```

也可以不激活环境，直接使用 `.venv\Scripts\python.exe` 和 `.venv\Scripts\uvicorn.exe` 执行对应命令。

## 4. 验证服务

服务启动后访问：

```text
http://localhost:8000/api/v1/health
```

Swagger API 文档地址：`http://localhost:8000/docs`。

数据库结构由 Alembic 管理。首次部署和每次更新代码后，执行 `alembic upgrade head`（UV 环境使用 `uv run alembic upgrade head`）同步迁移。

## 5. 生成演示数据

完成数据库迁移后，可以使用 `seed_demo_data.py` 生成用于登录和功能验证的演示数据。脚本可以重复执行，不会重复创建演示用户、家庭成员、账户、预算、流水或转账。

UV 环境：

```powershell
uv run python seed_demo_data.py
```

非 UV 环境（已激活 `.venv`）：

```powershell
python seed_demo_data.py
```

脚本会创建一个演示家庭、3 个用户、2 名管理员、1 名普通成员和 6 个有余额的账户，并补齐默认收支分类。

演示数据覆盖 2026 年 7 月和 8 月：每月每位用户 8 条收入/支出流水（工资、奖金、住房、餐饮、交通、购物、娱乐、医疗等），每月 3 条家庭内部转账；同时创建 7 月、8 月和 9 月的家庭预算及 3 位成员的个人预算，共 12 条预算。跨成员转账默认为 `PENDING_CONFIRM`，可用转入方账号登录后测试确认流程。

演示登录账号如下：

| 用户名 | 角色 | 密码 |
| --- | --- | --- |
| `admin_zhang` | 管理员 | `Demo@123456` |
| `admin_li` | 管理员 | `Demo@123456` |
| `member_wang` | 普通成员 | `Demo@123456` |
