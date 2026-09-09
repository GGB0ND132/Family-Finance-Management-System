# 前端部署说明

前端是基于 React、TypeScript 和 Vite 的家庭收支管理界面。建议使用 Node.js 20 LTS 或更高版本，并使用 npm 10 或更高版本。

## 1. 安装依赖

在 `frontend/` 目录执行：

```powershell
npm ci
```

## 2. 开发模式

```powershell
npm run dev
```

浏览器访问 Vite 输出的地址，默认是 `http://localhost:5173`。开发服务器会将 `/api` 请求代理到 `http://127.0.0.1:8000`，请先启动后端服务。

## 3. 构建和预览

生成生产构建文件：

```powershell
npm run build
```

构建结果位于 `dist/`。本地预览构建结果：

```powershell
npm run preview
```

正式部署时，将 `dist/` 部署到 Nginx、静态文件服务器或其他 Web 服务器，并将 `/api` 请求反向代理到后端服务地址。

## 4. 质量检查

提交前可运行：

```powershell
npm run lint
```
