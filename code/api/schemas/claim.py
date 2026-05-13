from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from api.models.claim import ClaimStatus


class ClaimOut(BaseModel):
    id: int
    user_id: int
    invoice_id: int
    description: Optional[str]
    status: ClaimStatus
    submitted_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class ClaimDetail(ClaimOut):
    """带发票信息的详情"""
    invoice_type: Optional[str] = None
    vendor: Optional[str] = None
    total: Optional[float] = None
    category: Optional[str] = None
    invoice_date: Optional[str] = None
    approval_records: List[dict] = []


class ApprovalRecordOut(BaseModel):
    id: int
    claim_id: int
    approver_id: int
    action: str
    comment: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
