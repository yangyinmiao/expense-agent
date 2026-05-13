from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from api.db import Base


class ClaimStatus(str, enum.Enum):
    draft = "draft"                       # 草稿
    pending = "pending"                   # 待主管审批
    manager_approved = "manager_approved" # 主管已通过，待财务
    finance_approved = "finance_approved" # 财务已通过，待打款
    rejected = "rejected"                 # 已驳回
    paid = "paid"                         # 已打款


class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, default="")
    status = Column(Enum(ClaimStatus), default=ClaimStatus.draft, nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    invoice = relationship("Invoice")
    approvals = relationship("ApprovalRecord", back_populates="claim")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("expense_claims.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)   # approved / rejected
    comment = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    claim = relationship("ExpenseClaim", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])
