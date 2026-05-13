#!/bin/bash
# ============================================================
# expense-agent 一键启动脚本
# 用法：./start.sh
# ============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/venv"
FRONTEND="$PROJECT_DIR/frontend"
DEPLOY="$PROJECT_DIR/deploy"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  💰 expense-agent 启动中..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Docker 基础服务
echo ""
echo "▶ [1/3] 启动 Docker 服务（PostgreSQL / Redis / MinIO）..."
docker compose -f "$DEPLOY/docker-compose.yml" up -d
echo "✅ Docker 服务已启动"

# 2. 等待 PostgreSQL 就绪
echo ""
echo "⏳ 等待 PostgreSQL 就绪..."
for i in $(seq 1 15); do
  if docker exec expense_postgres pg_isready -U expense -d expense_agent -q 2>/dev/null; then
    echo "✅ PostgreSQL 就绪"
    break
  fi
  sleep 1
done

# 3. 激活 venv 并执行 Alembic 迁移（幂等）
echo ""
echo "▶ [2/3] 执行数据库迁移..."
source "$VENV/bin/activate"
cd "$PROJECT_DIR"
alembic upgrade head
echo "✅ 数据库迁移完成"

# 4. 启动 FastAPI 后端（后台）
echo ""
echo "▶ [3/3] 启动后端 FastAPI（端口 8000）..."
uvicorn code.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "✅ 后端 PID: $BACKEND_PID"

# 5. 等待后端就绪
echo ""
echo "⏳ 等待后端就绪..."
for i in $(seq 1 20); do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端已就绪"
    break
  fi
  sleep 1
done

# 6. 启动前端 Vite（后台）
echo ""
echo "▶ 启动前端 React（端口 3000）..."
cd "$FRONTEND"
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端 PID: $FRONTEND_PID"

# 7. 汇总
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 全部服务已启动！"
echo ""
echo "  前端地址：  http://localhost:3000"
echo "  后端 API：  http://localhost:8000"
echo "  API 文档：  http://localhost:8000/docs"
echo "  MinIO 控制台：http://localhost:9001"
echo ""
echo "  停止所有服务：Ctrl+C 或运行 ./stop.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 捕获 Ctrl+C，优雅退出
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; docker compose -f $DEPLOY/docker-compose.yml stop; echo '已停止。'" SIGINT SIGTERM

# 保持前台等待
wait $BACKEND_PID $FRONTEND_PID
