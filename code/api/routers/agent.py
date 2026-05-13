"""
智能问答路由：自然语言查询报销数据
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.db import get_db
from api.models.user import User
from api.routers.auth import get_current_user
from api.services.expense_agent import build_expense_agent

router = APIRouter(prefix="/agent", tags=["智能问答"])


class ChatRequest(BaseModel):
    question: str


@router.post("/chat", summary="自然语言问答")
def chat(req: ChatRequest, db: Session = Depends(get_db),
         current_user: User = Depends(get_current_user)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        agent = build_expense_agent(
            db=db,
            current_user_id=current_user.id,
            current_user_role=current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        )
        result = agent.invoke({"input": req.question})
        answer = result.get("output", "抱歉，我无法回答这个问题。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行失败：{str(e)}")

    return {"question": req.question, "answer": answer}
