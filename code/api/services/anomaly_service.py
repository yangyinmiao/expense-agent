"""
异常检测服务：月度超限预警 + 重复发票检测
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from api.models.invoice import Invoice
from api.models.claim import ExpenseClaim, ClaimStatus

MONTHLY_LIMITS = {
    "餐饮": 3000,
    "交通": 10000,
    "住宿": 5000,
    "办公用品": 20000 * 5,  # 月度上限 = 单次 * 5
    "其他": 3000,
}


def check_monthly_anomaly(user_id: int, category: str,
                          amount: float, db: Session) -> dict:
    """检查单月同类别累计是否超限"""
    now = datetime.utcnow()
    monthly_total = (
        db.query(func.sum(Invoice.total))
        .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id)
        .filter(
            ExpenseClaim.user_id == user_id,
            Invoice.category == category,
            ExpenseClaim.status.notin_([ClaimStatus.rejected]),
            extract("year", ExpenseClaim.submitted_at) == now.year,
            extract("month", ExpenseClaim.submitted_at) == now.month,
        )
        .scalar() or 0
    )

    limit = MONTHLY_LIMITS.get(category, 3000)
    after_total = monthly_total + (amount or 0)

    return {
        "月度已报销": round(monthly_total, 2),
        "本次金额": round(amount or 0, 2),
        "月度上限": limit,
        "超限预警": after_total > limit,
        "超出金额": round(max(0, after_total - limit), 2),
    }
