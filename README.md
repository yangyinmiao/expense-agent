# 财务报销 Agent 🧾

一个基于 GPT-4o Vision 的智能财务报销助手，支持上传发票图片/PDF，自动识别信息并校验是否符合报销规定。

## 功能

- 📸 上传发票图片（JPG/PNG）或 PDF
- 🔍 自动识别：金额、日期、发票类型、供应商、费用类别等
- ✅ 规则校验：按公司报销规定自动审核
- 📄 生成报销摘要，支持下载

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（复制 .env.example 为 .env）
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY

# 3. 启动
streamlit run app.py
```

## 项目结构

```
expense-agent/
├── app.py          # Streamlit 主界面
├── extractor.py    # 发票信息提取（GPT-4o Vision）
├── validator.py    # 报销规则校验
├── requirements.txt
└── .env.example
```

## 后续可扩展

- [ ] 批量上传多张发票
- [ ] 对话式 Agent（用自然语言询问报销政策）
- [ ] 历史记录 & 统计报表
- [ ] 导出 Excel 报销单
