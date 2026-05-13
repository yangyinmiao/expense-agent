from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from api.db import get_db
from api.models.claim import ExpenseClaim, ApprovalRecord, ClaimStatus
from api.models.user import User, UserRole
from api.routers.auth import get_current_user

router = APIRouter(prefix="/claims", tags=["报销申请"])


# ---------- Schemas ----------
class CreateClaimRequest(BaseModel):
    invoice_id: int
    description: str = ""


class ApproveRequest(BaseModel):
    comment: str = ""


class RejectRequest(BaseModel):
    comment: str


# ---------- Routes ----------
@router.post("/", summary="创建报销申请（草稿）")
def create_claim(req: CreateClaimRequest, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    claim = ExpenseClaim(
        user_id=current_user.id,
        invoice_id=req.invoice_id,
        description=req.description,
        status=ClaimStatus.draft,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return {"claim_id": claim.id, "status": claim.status}


@router.post("/{claim_id}/submit", summary="提交审批")
def submit_claim(claim_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    if claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if claim.status != ClaimStatus.draft:
        raise HTTPException(status_code=400, detail="只有草稿状态可以提交")
    claim.status = ClaimStatus.pending
    claim.submitted_at = datetime.utcnow()
    db.commit()
    return {"claim_id": claim.id, "status": claim.status}


@router.post("/{claim_id}/approve", summary="审批通过")
def approve_claim(claim_id: int, req: ApproveRequest = ApproveRequest(),
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")

    # 权限检查：主管审批 pending，财务审批 manager_approved
    next_status_map = {
        ClaimStatus.pending: (UserRole.manager, ClaimStatus.manager_approved),
        ClaimStatus.manager_approved: (UserRole.finance, ClaimStatus.finance_approved),
    }
    if claim.status not in next_status_map:
        raise HTTPException(status_code=400, detail=f"当前状态 {claim.status} 无法审批")

    required_role, next_status = next_status_map[claim.status]
    if current_user.role not in (required_role, UserRole.admin):
        raise HTTPException(status_code=403, detail=f"需要 {required_role} 角色才能审批此步骤")

    claim.status = next_status
    record = ApprovalRecord(claim_id=claim_id, approver_id=current_user.id,
                            action="approved", comment=req.comment)
    db.add(record)
    db.commit()
    return {"claim_id": claim_id, "status": claim.status}


@router.post("/{claim_id}/reject", summary="驳回申请")
def reject_claim(claim_id: int, req: RejectRequest,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    if current_user.role not in (UserRole.manager, UserRole.finance, UserRole.admin):
        raise HTTPException(status_code=403, detail="无权驳回")
    claim.status = ClaimStatus.rejected
    record = ApprovalRecord(claim_id=claim_id, approver_id=current_user.id,
                            action="rejected", comment=req.comment)
    db.add(record)
    db.commit()
    return {"claim_id": claim_id, "status": "rejected", "reason": req.comment}


@router.get("/my", summary="我的报销申请列表")
def my_claims(db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    from api.models.invoice import Invoice
    claims = db.query(ExpenseClaim).filter(
        ExpenseClaim.user_id == current_user.id
    ).order_by(ExpenseClaim.id.desc()).all()
    result = []
    for c in claims:
        inv = db.query(Invoice).filter(Invoice.id == c.invoice_id).first()
        result.append({
            "id": c.id, "status": c.status, "description": c.description,
            "submitted_at": c.submitted_at, "invoice_id": c.invoice_id,
            "vendor": inv.vendor if inv else None,
            "total": inv.total if inv else None,
            "category": inv.category if inv else None,
            "invoice_date": str(inv.invoice_date) if inv and inv.invoice_date else None,
        })
    return result


@router.get("/pending", summary="待审批列表（主管/财务用）")
def pending_claims(db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    from api.models.invoice import Invoice
    if current_user.role not in (UserRole.manager, UserRole.finance, UserRole.admin):
        raise HTTPException(status_code=403, detail="无权查看")
    if current_user.role == UserRole.manager:
        status_filter = ClaimStatus.pending
    elif current_user.role == UserRole.finance:
        status_filter = ClaimStatus.manager_approved
    else:
        # admin 看所有待审批
        claims = db.query(ExpenseClaim).filter(
            ExpenseClaim.status.in_([ClaimStatus.pending, ClaimStatus.manager_approved])
        ).order_by(ExpenseClaim.submitted_at).all()
        return _enrich_claims(claims, db)

    claims = db.query(ExpenseClaim).filter(
        ExpenseClaim.status == status_filter
    ).order_by(ExpenseClaim.submitted_at).all()
    return _enrich_claims(claims, db)


def _enrich_claims(claims, db):
    """给 claim 列表附加发票字段"""
    from api.models.invoice import Invoice
    result = []
    for c in claims:
        inv = db.query(Invoice).filter(Invoice.id == c.invoice_id).first()
        result.append({
            "id": c.id, "user_id": c.user_id, "invoice_id": c.invoice_id,
            "status": c.status, "description": c.description,
            "submitted_at": c.submitted_at,
            "vendor": inv.vendor if inv else None,
            "total": inv.total if inv else None,
            "category": inv.category if inv else None,
            "invoice_date": str(inv.invoice_date) if inv and inv.invoice_date else None,
            "invoice_type": inv.invoice_type if inv else None,
        })
    return result


@router.get("/{claim_id}", summary="申请详情")
def get_claim(claim_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    if claim.user_id != current_user.id and current_user.role not in (
        UserRole.manager, UserRole.finance, UserRole.admin
    ):
        raise HTTPException(status_code=403, detail="无权查看")
    return claim


@router.get("/{claim_id}/detail", summary="申请详情（含发票原件 URL + 审批记录）")
def claim_detail(claim_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    from api.services.storage_service import get_presigned_url
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")

    can_view = (
        claim.user_id == current_user.id
        or current_user.role in (UserRole.manager, UserRole.finance, UserRole.admin)
    )
    if not can_view:
        raise HTTPException(status_code=403, detail="无查看权限")

    invoice = claim.invoice
    try:
        raw_url = get_presigned_url(invoice.file_id, expires_days=1)
        image_url = raw_url.replace("http://localhost:9000", "/minio")
    except Exception:
        image_url = (invoice.oss_url or "").replace("http://localhost:9000", "/minio")

    approvals = []
    for ap in sorted(claim.approvals, key=lambda x: x.created_at or 0):
        approvals.append({
            "approver_id": ap.approver_id,
            "approver_name": ap.approver.name if ap.approver else "—",
            "action": ap.action,
            "comment": ap.comment,
            "created_at": ap.created_at.isoformat() if ap.created_at else None,
        })

    return {
        "claim": {
            "id": claim.id,
            "status": claim.status,
            "description": claim.description,
            "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
            "user_id": claim.user_id,
            "user_name": claim.user.name if claim.user else "—",
        },
        "invoice": {
            "id": invoice.id,
            "invoice_type": invoice.invoice_type,
            "invoice_number": invoice.invoice_number,
            "vendor": invoice.vendor,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "amount": invoice.amount,
            "tax": invoice.tax,
            "total": invoice.total,
            "category": invoice.category,
            "raw_json": invoice.raw_json,
            "image_url": image_url,
            "file_id": invoice.file_id,
        },
        "approvals": approvals,
    }
