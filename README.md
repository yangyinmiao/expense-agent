# 💰 Expense Agent — 中小企业财务报销系统

> 面向 500 人规模企业的智能报销 Agent，支持发票 OCR 识别、规则校验、多角色审批流程、AI 异常检测与对话式查询。

---

## ✨ 功能亮点

| 模块 | 功能 |
|------|------|
| **发票上传** | 单张/批量上传，GPT-4o OCR 自动提取金额、供应商、开票日期等字段 |
| **规则校验** | 按类别校验单次上限（餐饮 2000、办公用品 20000 等），违规自动拦截 |
| **审批流程** | 员工提交 → 主管审批 → 财务复核，四角色 RBAC 权限隔离 |
| **发票原件预览** | 图片 inline 展示，PDF 用 iframe 内嵌预览+下载 |
| **AI 异常检测** | 自动标记重复发票、超额申请、可疑供应商 |
| **我的审批记录** | 主管/财务可查看历史审批列表、通过率统计 |
| **报表分析** | 月度趋势、类别分布、部门对比（Recharts 图表） |
| **Agent 对话** | LangChain Agent + 6 个工具，自然语言查询报销数据 |

---

## 🏗️ 技术栈

**后端**
- Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic
- PostgreSQL 15 · Redis 7 · MinIO（本地 OSS）
- LangChain + GPT-4o（OCR + Agent）

**前端**
- React 18 + TypeScript + Vite
- Ant Design 5 + React Query + React Router v6

**部署**
- Docker Compose（PostgreSQL / Redis / MinIO）
- 本地开发：uvicorn --reload + Vite dev server

---

## 🚀 快速启动

### 前置条件

```bash
# macOS
brew install poppler          # PDF 解析
# 已安装：Docker Desktop、Node.js 18+、Python 3.11
```

### 一键启动

```bash
git clone https://github.com/yangyinmiao/expense-agent.git
cd expense-agent

# 安装后端依赖（首次）
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖（首次）
cd frontend && npm install && cd ..

# 一键启动所有服务
chmod +x start.sh
./start.sh
```

启动后访问：

| 地址 | 说明 |
|------|------|
| http://localhost:3000 | 前端页面 |
| http://localhost:8000/docs | 后端 Swagger API 文档 |
| http://localhost:9001 | MinIO 控制台（minioadmin / minioadmin） |

### 停止服务

```bash
./stop.sh
# 或在 start.sh 终端按 Ctrl+C
```

---

## 🔧 手动启动（分步）

```bash
# 1. Docker 基础服务
docker compose -f deploy/docker-compose.yml up -d

# 2. 后端
source venv/bin/activate
uvicorn code.main:app --reload --port 8000

# 3. 前端（另开终端）
cd frontend && npm run dev
```

---

## 👥 测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 系统管理员 |
| zhangsan | pass123 | 员工 |
| manager_zhang | pass123 | 主管（可审批） |
| finance_wang | pass123 | 财务（可复核） |

---

## 📁 项目结构

```
expense-agent/
├── code/
│   ├── api/
│   │   └── routers/        # auth / invoices / claims / admin / agent
│   ├── core/
│   │   ├── extractor.py    # GPT-4o OCR 发票解析
│   │   ├── validator.py    # 报销规则校验
│   │   ├── anomaly_service.py  # AI 异常检测
│   │   └── agent_service.py   # LangChain Agent + 工具
│   ├── models/             # SQLAlchemy ORM 模型
│   ├── schemas/            # Pydantic 请求/响应模型
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── pages/          # Login / Submit / Batch / MyClaims / Pending / Reports / AgentChat / ApprovalHistory
│   │   ├── components/     # AppLayout / ClaimDetailModal
│   │   ├── api/            # axios 封装
│   │   └── context/        # AuthContext
│   └── vite.config.ts      # /minio/ 代理配置
├── deploy/
│   └── docker-compose.yml
├── docs/
│   ├── DESIGN.md
│   ├── USER_MANUAL.md
│   └── plans/
├── alembic/                # 数据库迁移
├── start.sh                # 一键启动
└── stop.sh                 # 一键停止
```

---

## 📌 环境变量

复制 `.env.example` 为 `.env`（如有），或直接使用默认值：

```env
POSTGRES_DB=expense_agent
POSTGRES_USER=expense
POSTGRES_PASSWORD=changeme
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://your-endpoint/v1
```

---

## 🗺️ 后续规划

- [ ] 多币种支持（currency 字段 + 实时汇率 API）
- [ ] AI 成本优化建议（GPT 分析报表 + 预算对比）
- [ ] 报销政策实时解读（RAG + 定时爬取国税局文件）
