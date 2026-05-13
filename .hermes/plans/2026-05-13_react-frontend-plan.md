# 迁移到 React 前端 — 实施计划

日期：2026-05-13
目标：把当前 Streamlit 前端替换为一个专业、可维护的 React + TypeScript 前端，视觉风格采用蓝白配色，提升交互体验、可扩展性与企业级感。

背景与假设
- 后端（FastAPI）接口已基本完备：/auth, /invoices, /claims, /admin, /agent 等。
- 当前项目工作目录：~/Documents/Development/PersonalProjects/expense-agent
- 当前代码用 Python 管理，部署以 Docker Compose 为主。前端可作为独立项目（frontend/）或被打包放入 deploy 静态主机。
- 目标是增量迁移：先做独立 React 前端并在本地联调（Vite + dev proxy），确认后再替换 Streamlit 或并行存在。

总体方案（高层）
1. 使用 Vite + React + TypeScript 脚手架（快速、现代、极佳 DX）。
2. UI 库：Ant Design（企业感强、中文文档好）或 Mantine（更现代）；推荐 Ant Design（antd）搭配定制主题实现蓝白配色。
3. 状态与数据：react-query（TanStack Query）管理远程数据缓存，Context/Zustand 管理全局 auth/session
4. 网络层：axios（带拦截器统一注入 token、错误处理、重试）
5. 图表：react-plotly.js 或 Recharts。因为后端已有 Plotly 风格图表，优先 react-plotly.js 可复用现有图配置。
6. 验证与表单：react-hook-form + antd 表单组件。
7. 本地开发：Vite dev server + proxy 到 http://localhost:8000（避免 CORS 问题）
8. 代码质量：TypeScript 严格模式、ESLint (Airbnb/Standard) + Prettier、husky + lint-staged
9. 测试：单元（vitest）+ E2E（Cypress/Playwright）
10. 部署：构建产物到 frontend/dist，部署到 Nginx（Docker）或用 Dockerfile 构建静态镜像并加入 docker-compose。

重要设计/安全点
- JWT 不建议在 localStorage 明文保存：优先选项为后端设置 httpOnly cookie（如果后端能支持）。若后端继续返回 token，前端用内存 +刷新策略（refresh token 存 httpOnly cookie）或短期 token +刷新机制。
- 大文件上传（发票）需支持 200MB/单文件：前端实现分片或直接 POST（后端需支持）。现阶段先实现普通上传，后续按需加分片。
- 文件预览（Image/PDF）在浏览器内展示缩略图，点击可弹窗查看原图。
- 批量上传采用 FormData 多文件 POST，显示进度条与每项状态。
- 智能问答（/agent/chat）用 HTTP POST（短交互）或 WebSocket/Server-Sent Events（若要流式返回）。先用 HTTP Polling 快速交付。

步骤清单（可直接执行）

1) 脚手架（1h）
- 在项目根创建 frontend/
- 命令：
  - pnpm create vite frontend --template react-ts
  - cd frontend && pnpm install
- 安装依赖：
  - pnpm add antd axios @tanstack/react-query react-router-dom react-plotly.js plotly.js react-hook-form dayjs
  - 开发依赖：pnpm add -D eslint prettier husky lint-staged vitest cypress

2) 项目骨架（2-4h）
- 目录结构：
  - frontend/
    - src/
      - api/ (axios 实例、接口封装)
      - components/ (Button, UploadCard, InvoicePreview, Badge, Layout)
      - pages/ (Login, Register, Submit, BatchUpload, MyClaims, Pending, Reports, AgentChat)
      - routes/ (React Router 配置)
      - store/ (AuthContext or Zustand)
      - styles/ (theme.less for antd 自定义)
      - App.tsx, main.tsx
- 实现全局 Layout（侧边栏 + 顶栏），将蓝白主题写入 antd less 变量或 CSS variables

3) Auth 流（2-3h）
- Login 页面：表单提交 /auth/login，保存 token 到内存 context 并设置 axios 拦截器
- 注册页面：/auth/register
- 实现 ProtectedRoute（无 token 重定向到登录）
- 实现退出登录，清理 state

4) 发票上传页（3-6h）
- Submit 页面：单文件上传 -> POST /invoices/upload -> 显示识别结果并调用 /claims/ 创建并提交
- 批量上传页面：多文件 FormData POST /invoices/batch-upload -> 显示每项识别/提交状态（成功/失败/详情）
- 文件预览（图片 / PDF）

5) 报销与审批（3-5h）
- 我的申请页：GET /claims/my，表格/卡片展示
- 待审批页：GET /claims/pending （管理权限）并支持审批/驳回操作
- 详情页：/claims/:id，显示发票、审批记录、操作按钮

6) 统计页（2-4h）
- 调用 /admin/stats/*，用 react-plotly.js 渲染图表（复用现有 Plotly 配置）
- 表格下载 CSV（可选）

7) 智能问答（2-4h）
- 前端聊天 UI（简单版）：输入框 -> POST /agent/chat -> 显示回答历史
- 用 loading 状态，支持复制/导出答案

8) 工具链与质量（2-4h）
- ESLint + Prettier + husky pre-commit
- React Query 全局 provider，统一错误提示（message 弹窗）
- 单元测试（关键组件）、E2E 覆盖主要流程（登录 -> 上传 -> 提交 -> 审批）

9) 打包与部署（1-2h）
- 增加 Dockerfile（基于 nginx）:
  - build -> nginx 静态
- 更新 deploy/docker-compose.yml，加入 frontend 服务（镜像或本地构建）

文件清单（重要）
- frontend/package.json
- frontend/Vite config
- frontend/src/main.tsx
- frontend/src/App.tsx
- frontend/src/api/axios.ts
- frontend/src/api/auth.ts, invoices.ts, claims.ts, admin.ts, agent.ts
- frontend/src/pages/*
- frontend/Dockerfile
- deploy/docker-compose.frontend.yml（可选）

验证与验收标准
- 本地开发：pnpm dev（Vite）能连通后端（通过 proxy）
- 功能：登录/注册、单发票上传、批量上传、提交申请、审批通过/驳回、统计图可正常渲染、智能问答返回内容
- UI：蓝白主题统一、侧栏折叠可展开、文件上传支持 200MB（若后端支持）
- 安全：token 不存 localStorage；若后端改为 httpOnly cookie，前端自动受益

风险与权衡
- 工作量：完整迁移预计 3–6 个工作日（取决于细节与测试覆盖）。
- API 不兼容：若后端需要变化（如 httpOnly cookie），需后端配合修改。
- Streamlit demo 将被替换：若需要同时保留两个前端，需额外维护两套代码。

后续建议
- 用 Storybook 做组件库，方便视觉统一与复用
- 在首次上线前做一次小范围用户可用性测试，收集 UI/文字的局部优化意见
- 日后考虑使用企业级设计系统（Ant Design Pro）以缩短开发时间

---

是否要我现在：
- A）直接在仓库里 scaffold frontend（生成 Vite 项目、安装依赖、提交初始 PR）并实现最小可用版（登录 + 提交单张发票 + my claims）？
- B）先只生成详细任务分解（含每个 PR 的文件改动清单与测试用例）供你审批？

回复 A 或 B（或提出其它偏好），我就开始下一步。