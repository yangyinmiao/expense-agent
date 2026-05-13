#!/bin/bash
# ============================================================
# expense-agent 一键停止脚本
# ============================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "正在停止所有服务..."

# 停止前端 & 后端进程
pkill -f "uvicorn code.main:app" 2>/dev/null && echo "✅ 后端已停止" || echo "⚠️  后端未在运行"
pkill -f "vite" 2>/dev/null && echo "✅ 前端已停止" || echo "⚠️  前端未在运行"

# 停止 Docker 服务
docker compose -f "$PROJECT_DIR/deploy/docker-compose.yml" stop
echo "✅ Docker 服务已停止"
