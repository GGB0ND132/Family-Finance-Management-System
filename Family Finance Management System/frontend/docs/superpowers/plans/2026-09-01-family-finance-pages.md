# Family Finance Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a usable front-end demonstration for authentication, dashboard, transaction and budget workflows.

**Architecture:** React Router separates authentication from the persistent application shell. A typed in-memory Zustand store supplies demonstration data and mutation points, while page components derive their own summaries and can later consume REST query hooks without changing the view contract.

**Tech Stack:** React 19, TypeScript, Vite, Ant Design 6, React Router 7, Zustand 5, ECharts.

**Spec:** `../需求与架构设计.md`

## Global Constraints

- UI library: Ant Design 6.6.2.
- The server API remains `/api/v1`; this iteration uses no network requests.
- Amounts display to two decimal places.
- Budget warning begins at 80%; over-budget begins above 100%.
- Mobile layout must preserve navigation and table access.

---

### Task 1: Product shell and local financial model

**Files:**
- Create: `src/data/financeData.ts`
- Create: `src/stores/financeStore.ts`
- Create: `src/layouts/AppLayout.tsx`
- Modify: `src/App.tsx`, `src/main.tsx`, `src/index.css`

**Interfaces:**
- Produces `useFinanceStore`, `accounts`, `categories`, `budgetItems` and `transactions` for page components.
- Produces `AppLayout` with an `<Outlet />` for authenticated routes.

- [x] Create domain types and fixed family data.
- [x] Create transaction and budget mutation methods in Zustand.
- [x] Configure routes and application navigation.
- [x] Verify `npm run build` succeeds.

### Task 2: Login and dashboard

**Files:**
- Create: `src/pages/LoginPage.tsx`
- Create: `src/pages/DashboardPage.tsx`
- Modify: `src/App.css`

**Interfaces:**
- Consumes `useFinanceStore` transaction and budget state.
- Produces `/login` and `/dashboard` routes.

- [x] Implement validated login form that routes to the dashboard.
- [x] Add summary, budget progress, recent transactions and two report charts.
- [x] Verify `npm run lint` and `npm run build` succeed.

### Task 3: Transaction and budget workflows

**Files:**
- Create: `src/pages/TransactionsPage.tsx`
- Create: `src/pages/BudgetsPage.tsx`
- Modify: `src/App.css`

**Interfaces:**
- Consumes `useFinanceStore.addTransaction` and `useFinanceStore.updateBudget`.
- Produces `/transactions` and `/budgets` routes.

- [x] Add client-side filtering and an Ant Design Drawer-based transaction form.
- [x] Add category budget editing with warning and over-budget states.
- [x] Verify build and lint; browser screenshot automation was blocked by the workspace path parser.
