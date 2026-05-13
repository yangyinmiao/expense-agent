"""
管理员接口：统计报表、规则管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel

from api.db import get_db
from api.models.invoice import Invoice
from api.models.claim import ExpenseClaim, ClaimStatus
from api.models.user import User, UserRole
from api.models.rule import ExpenseRule
from api.routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["管理员"])


def require_admin_or_finance(current_user: User = Depends(get_current_user)):
    if current_user.role not in (UserRole.admin, UserRole.finance):
        raise HTTPException(status_code=403, detail="需要管理员或财务权限")
    return current_user


@router.get("/stats/monthly", summary="月度报销统计（按类别）")
def monthly_stats(year: int, month: int, db: Session = Depends(get_db),
                  _: User = Depends(require_admin_or_finance)):
    results = (
        db.query(Invoice.category,
                 func.count(ExpenseClaim.id).label("申请数"),
                 func.sum(Invoice.total).label("总金额"))
        .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id)
        .filter(
            ExpenseClaim.status == ClaimStatus.finance_approved,
            extract("year", ExpenseClaim.submitted_at) == year,
            extract("month", ExpenseClaim.submitted_at) == month,
        )
        .group_by(Invoice.category)
        .all()
    )
    return [{"类别": r[0], "申请数": r[1], "总金额": round(r[2] or 0, 2)} for r in results]


@router.get("/stats/department", summary="月度报销统计（按部门）")
def department_stats(year: int, month: int, db: Session = Depends(get_db),
                     _: User = Depends(require_admin_or_finance)):
    results = (
        db.query(User.department,
                 func.count(ExpenseClaim.id).label("申请数"),
                 func.sum(Invoice.total).label("总金额"))
        .join(ExpenseClaim, ExpenseClaim.user_id == User.id)
        .join(Invoice, Invoice.id == ExpenseClaim.invoice_id)
        .filter(
            ExpenseClaim.status == ClaimStatus.finance_approved,
            extract("year", ExpenseClaim.submitted_at) == year,
            extract("month", ExpenseClaim.submitted_at) == month,
        )
        .group_by(User.department)
        .all()
    )
    return [{"部门": r[0], "申请数": r[1], "总金额": round(r[2] or 0, 2)} for r in results]


@router.get("/stats/trend", summary="年度月度趋势（按月汇总）")
def yearly_trend(year: int, db: Session = Depends(get_db),
                 _: User = Depends(require_admin_or_finance)):
    results = (
        db.query(extract("month", ExpenseClaim.submitted_at).label("月份"),
                 func.count(ExpenseClaim.id).label("申请数"),
                 func.sum(Invoice.total).label("总金额"))
        .join(Invoice, Invoice.id == ExpenseClaim.invoice_id)
        .filter(
            ExpenseClaim.status == ClaimStatus.finance_approved,
            extract("year", ExpenseClaim.submitted_at) == year,
        )
        .group_by(extract("month", ExpenseClaim.submitted_at))
        .order_by(extract("month", ExpenseClaim.submitted_at))
        .all()
    )
    return [{"月份": int(r[0]), "申请数": r[1], "总金额": round(r[2] or 0, 2)} for r in results]


# ---------- 规则管理 ----------
class RuleUpdateRequest(BaseModel):
    max_amount: float
    description: str = ""


@router.get("/rules", summary="查询所有报销规则")
def list_rules(db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    return db.query(ExpenseRule).all()


@router.put("/rules/{category}", summary="更新报销规则")
def update_rule(category: str, req: RuleUpdateRequest,
                db: Session = Depends(get_db),
                current_user: User = Depends(require_admin_or_finance)):
    rule = db.query(ExpenseRule).filter(ExpenseRule.category == category).first()
    if rule:
        rule.max_amount = req.max_amount
        rule.description = req.description
        rule.updated_by = current_user.id
    else:
        rule = ExpenseRule(category=category, max_amount=req.max_amount,
                           description=req.description, updated_by=current_user.id)
        db.add(rule)
    db.commit()
    return {"category": category, "max_amount": req.max_amount}
