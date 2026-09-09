# 家庭收支管理系统

家庭收支管理系统（管家婆）用于记录和管理家庭成员的收入、支出、账户与预算，并提供查询、统计、报表导出和数据导入功能。

## 项目组成

- `backend/`：FastAPI 后端 API、数据库模型与 Alembic 迁移
- `frontend/`：React + TypeScript 前端界面
- `docs/`：项目设计和开发文档

## 技术栈

- 后端：Python 3.11+、FastAPI、SQLAlchemy、Alembic、MySQL
- 前端：React 19、TypeScript、Vite、Ant Design、ECharts

## 快速启动

1. 按 [后端部署说明](backend/README.md) 准备 MySQL、环境变量并启动 API 服务。
2. 按 [前端部署说明](frontend/README.md) 安装 Node.js 依赖并启动前端开发服务器。
3. 浏览器访问 `http://localhost:5173`。

后端 API 前缀为 `/api/v1`，健康检查地址为 `http://localhost:8000/api/v1/health`。
