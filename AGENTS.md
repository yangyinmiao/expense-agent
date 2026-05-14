# AGENTS.md — expense-agent 项目指南

> 本文件为 AI Agent（Hermes、Claude Code、Codex 等）提供项目上下文，帮助快速理解代码结构、运行方式和开发规范。每次进入项目时请优先阅读。

---

## 项目概述

**expense-agent** 是一个面向中小企业的智能财务报销系统，支持发票 OCR 识别、多角色审批流程、AI 异常检测和自然语言查询。

- **后端**：FastAPI + SQLAlchemy + PostgreSQL + Redis + MinIO
- **前端**：React 18 + TypeScript + Vite + Ant Design 5 + Recharts
- **AI**：GPT-4o（OCR + Agent）+ LangChain

---

## 目录结构

```
expense-agent/
├── code/                        # Python 后端
│   ├── __init__.py              # 必须存在，使 code/ 成为 package
│   ├── app.py                   # Streamlit 遗留入口（不用）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 应用入口，uvicorn 启动点
│   │   ├── db.py                # SQLAlchemy engine / session / Base
│   │   ├── models/              # ORM 模型
│   │   │   ├── user.py          # User, UserRole
│   │   │   ├── invoice.py       # Invoice
│   │   │   ├── claim.py         # ExpenseClaim, ApprovalRecord, ClaimStatus
│   │   │   └── rule.py          # 报销规则（数据库版）
│   │   ├── routers/             # FastAPI 路由
│   │   │   ├── auth.py          # /auth/login, /auth/register
│   │   │   ├── invoices.py      # /invoices/upload, /invoices/batch-upload
│   │   │   ├── claims.py        # /claims/* 报销申请 CRUD + 审批
│   │   │   ├── admin.py         # /admin/stats/* 统计报表
│   │   │   └── agent.py         # /agent/chat 自然语言问答
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   └── services/
│   │       ├── expense_agent.py # LangChain Agent，6个工具
│   │       ├── anomaly_service.py # 异常检测：月超限 + 重复发票
│   │       └── storage_service.py # MinIO 文件存储
│   ├── core/
│   │   ├── extractor.py         # GPT-4o OCR，支持图片和 PDF
│   │   └── validator.py         # 报销规则校验（单次上限）
│   ├── config/
│   │   └── settings.py          # 统一环境变量管理
│   └── migrations/              # Alembic 迁移脚本
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Submit.tsx       # 单张发票上传+报销
│   │   │   ├── BatchUpload.tsx  # 批量上传
│   │   │   ├── MyClaims.tsx     # 我的申请列表
│   │   │   ├── Pending.tsx      # 待审批（主管/财务）
│   │   │   ├── ApprovalHistory.tsx # 已审批记录
│   │   │   ├── Reports.tsx      # 统计报表（Recharts）
│   │   │   └── AgentChat.tsx    # 智能问答
│   │   ├── components/
│   │   │   ├── AppLayout.tsx    # 侧边栏导航 + 布局
│   │   │   └── ClaimDetailModal.tsx # 申请详情弹窗
│   │   ├── api/
│   │   │   ├── axios.ts         # axios 实例，baseURL=/api，自动带 token
│   │   │   ├── claims.ts        # 报销相关接口
│   │   │   └── admin.ts         # 统计相关接口
│   │   ├── context/
│   │   │   └── AuthContext.tsx  # 登录态全局管理
│   │   └── App.tsx              # 路由配置
│   └── vite.config.ts           # 代理：/api→后端8000, /minio→MinIO9000
├── deploy/
│   └── docker-compose.yml       # PostgreSQL + Redis + MinIO
├── code/alembic.ini             # alembic 配置，script_location=migrations
├── start.sh                     # 一键启动脚本
├── stop.sh                      # 一键停止脚本
└── .env                         # 环境变量（不入 git）
```

---

## 快速启动

```bash
# 首次安装依赖
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 一键启动
./start.sh
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |
| MinIO 控制台 | http://localhost:9001 |

### 分步启动

```bash
# 1. 基础服务
docker compose -f deploy/docker-compose.yml up -d

# 2. 数据库迁移（alembic.ini 在 code/ 子目录，必须显式指定路径）
source venv/bin/activate
alembic -c code/alembic.ini upgrade head

# 3. 后端（从项目根目录启动，入口是 code/api/main.py）
uvicorn code.api.main:app --reload --port 8000

# 4. 前端（另开终端）
cd frontend && npm run dev
```

---

## 环境变量

`.env` 文件放在项目根目录：

```env
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://goods.fatrabbits.shop:12788/v1
OPENAI_MODEL=gpt-4o

DATABASE_URL=postgresql://expense:changeme@localhost:5432/expense_agent
REDIS_URL=redis://localhost:6379

MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

POSTGRES_DB=expense_agent
POSTGRES_USER=expense
POSTGRES_PASSWORD=changeme
```

---

## 数据模型

### 用户角色（UserRole）
| 角色 | 权限 |
|------|------|
| `employee` | 提交报销申请 |
| `manager` | 审批 `pending` 状态的申请 |
| `finance` | 审批 `manager_approved` 状态的申请 |
| `admin` | 查看所有数据，统计报表 |

### 审批流程（ClaimStatus）
```
draft → pending → manager_approved → finance_approved → paid
                                   ↘ rejected（任意阶段可驳回）
```

### 测试账号（密码均为 test123456）
| 用户名 | 角色 | ID |
|--------|------|----|
| 员工小李 | employee | 6 |
| 主管张经理 | manager | 7 |
| 财务王姐 | finance | 8 |
| 管理员Admin | admin | 9 |

---

## API 路由规范

### ⚠️ 路由顺序陷阱
FastAPI 按注册顺序匹配路由。**具体路径必须在通配路径之前注册**，否则会被错误匹配：

```python
# ✅ 正确顺序
@router.get("/pending")           # 具体路径先注册
@router.get("/approval-history")  # 具体路径先注册
@router.get("/{claim_id}")        # 通配路径放最后

# ❌ 错误：/{claim_id} 在前会把 "pending" 当作 claim_id
```

### 主要接口
```
POST /auth/login                     # 登录，返回 JWT token
POST /auth/register                  # 注册

POST /invoices/upload                # 上传单张发票（OCR 识别）
POST /invoices/batch-upload          # 批量上传

POST /claims/                        # 创建报销申请（草稿）
POST /claims/{id}/submit             # 提交审批
POST /claims/{id}/approve            # 审批通过
POST /claims/{id}/reject             # 驳回
GET  /claims/pending                 # 待审批列表（主管/财务）
GET  /claims/approval-history        # 我的审批历史
GET  /claims/{id}/detail             # 申请详情（含发票原件 URL）

GET  /admin/stats/monthly            # 月度类别统计
GET  /admin/stats/department         # 月度部门统计
GET  /admin/stats/trend              # 年度月度趋势

POST /agent/chat                     # 自然语言问答
```

---

## 前端开发规范

### 图表库
使用 **Recharts**，不使用 Plotly。Plotly/react-plotly.js 在 Vite + ESM 环境下有 CJS 兼容问题（`createPlotlyComponent is not a function`）。

```tsx
// ✅ 使用 Recharts
import { BarChart, Bar, PieChart, Pie, LineChart, Line, ResponsiveContainer } from 'recharts'

// ❌ 不要用
import createPlotlyComponent from 'react-plotly.js/factory'
```

### MinIO 图片访问
MinIO presigned URL 需要通过 Vite 代理 `/minio` 路径转发，避免 CORS 问题：

```typescript
// vite.config.ts 已配置
// /minio/* → http://localhost:9000/*
```

### 认证
`AuthContext` 管理登录态，`axios.ts` 自动在请求头注入 `Authorization: Bearer <token>`。

---

## 核心业务逻辑

### 发票 OCR（`core/extractor.py`）
- 支持 JPG/PNG/WEBP 图片和 PDF
- 调用 GPT-4o Vision，返回结构化字段：发票类型、开票日期、价税合计、供应商、费用类别
- PDF 先用 `pdf2image` 转成图片再识别

### 规则校验（`core/validator.py`）
单次报销上限：餐饮 2000、交通 2000、住宿 800、办公用品 20000、其他 500

### 异常检测（`services/anomaly_service.py`）
- 月度超限预警：同类别当月累计金额超限
- 重复发票检测：相同供应商 + 相同金额 + 同月

### LangChain Agent（`services/expense_agent.py`）
6 个工具：`get_my_claims_summary`、`get_pending_claims`、`get_expense_by_category`、`get_department_stats`、`get_monthly_trend`、`search_claims_by_keyword`

---

## 已知坑点

| 问题 | 解决方案 |
|------|----------|
| `code/` 不是 Python package | 已加 `code/__init__.py`，不要删 |
| alembic 找不到配置 | 始终用 `alembic -c code/alembic.ini upgrade head` |
| uvicorn 模块路径 | 入口是 `code.api.main:app`，不是 `code.main:app` |
| FastAPI 路由顺序 | `/pending`、`/approval-history` 必须在 `/{claim_id}` 前面 |
| react-plotly.js 白屏 | 已换成 Recharts，不要再引入 plotly |
| bcrypt verify 报错 | 用 `bcrypt.checkpw()` 直接校验，不用 `pwd_context.verify()` |
| MinIO CORS | 前端通过 `/minio` 代理访问，不要直连 9000 端口 |

---

## 代码提交规范

- commit message 用**中文**
- 格式：`<类型>: <说明>`
- 类型：`feat`（新功能）、`fix`（修复）、`refactor`（重构）、`docs`（文档）、`chore`（构建/配置）

```bash
# 示例
git commit -m "fix: 修复 approval-history 路由被 /{claim_id} 拦截的问题"
git commit -m "feat: 新增已审批记录页面及侧边栏入口"
```
