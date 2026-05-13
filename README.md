# 财务报销 Agent 🧾

一个基于 GPT-4o Vision 的智能财务报销助手，支持上传发票图片/PDF，自动识别信息并校验是否符合报销规定。

## 功能

- 📸 上传发票图片（JPG/PNG）或 PDF
- 🔍 自动识别：金额、日期、发票类型、供应商、费用类别等
- ✅ 规则校验：按公司报销规定自动审核
- 📄 生成报销摘要，支持下载

## 项目结构

```
expense-agent/
├── README.md
├── .env.example          # 环境变量模板
├── .gitignore
├── requirements.txt
├── docs/
│   └── DESIGN.md         # 系统设计文档
├── deploy/
│   ├── docker-compose.yml        # 一键启动 DB / Redis / MinIO
│   └── .env.deploy.example       # 部署环境变量模板
└── code/
    ├── app.py            # Streamlit 入口
    ├── core/             # 核心业务逻辑
    │   ├── extractor.py  # 发票识别（GPT-4o Vision）
    │   └── validator.py  # 报销规则校验
    └── config/           # 配置管理
        └── settings.py   # 统一读取环境变量
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY

# 3. 启动应用
streamlit run code/app.py
```

## 启动基础服务（可选，Phase 2 用）

```bash
cd deploy
cp .env.deploy.example .env
docker-compose up -d
# PostgreSQL: localhost:5432
# Redis:      localhost:6379
# MinIO:      localhost:9000（控制台 9001）
```

## 文档

- [系统设计文档](docs/DESIGN.md)
