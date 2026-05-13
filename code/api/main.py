"""
财务报销 Agent — FastAPI 主入口
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, invoices, claims, admin, agent

app = FastAPI(
    title="财务报销 Agent API",
    description="智能发票识别 + 报销流程管理",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(claims.router)
app.include_router(admin.router)
app.include_router(agent.router)


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "version": "0.2.0"}
