import os
import tempfile
import asyncio
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.models.invoice import Invoice
from api.services.storage_service import upload_file
from api.routers.auth import get_current_user
from api.models.user import User
from core.extractor import extract_invoice_info
from core.validator import validate_expense

router = APIRouter(prefix="/invoices", tags=["发票"])


@router.post("/upload", summary="上传发票并识别")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 读取文件内容
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB 限制
        raise HTTPException(status_code=413, detail="文件不能超过 10MB")

    # 2. 上传到 MinIO
    file_id, oss_url, file_hash = upload_file(content, file.filename)

    # 3. 保存临时文件用于 GPT 识别
    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        invoice_info = extract_invoice_info(tmp_path)
    finally:
        os.unlink(tmp_path)

    if "error" in invoice_info:
        raise HTTPException(status_code=422, detail=f"识别失败: {invoice_info['error']}")

    # 4. 重复发票检测
    inv_number = invoice_info.get("发票号码")
    if inv_number:
        existing = db.query(Invoice).filter(Invoice.invoice_number == inv_number).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"发票号 {inv_number} 已存在，请勿重复报销")

    # 5. 解析日期
    from datetime import date
    invoice_date = None
    raw_date = invoice_info.get("开票日期")
    if raw_date:
        try:
            invoice_date = date.fromisoformat(raw_date)
        except Exception:
            pass

    # 6. 存库
    invoice = Invoice(
        file_id=file_id,
        oss_url=oss_url,
        file_hash=file_hash,
        invoice_type=invoice_info.get("发票类型"),
        invoice_number=inv_number,
        vendor=invoice_info.get("供应商名称"),
        invoice_date=invoice_date,
        amount=invoice_info.get("金额（不含税）"),
        tax=invoice_info.get("税额"),
        total=invoice_info.get("价税合计"),
        category=invoice_info.get("费用类别"),
        raw_json=invoice_info,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # 7. 规则校验
    validation = validate_expense(invoice_info)

    return {
        "invoice_id": invoice.id,
        "file_id": file_id,
        "info": invoice_info,
        "validation": validation,
    }


@router.post("/batch-upload", summary="批量上传发票（并发识别）")
async def batch_upload_invoices(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="每次最多批量上传 10 张发票")

    async def process_one(file: UploadFile) -> dict:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            return {"filename": file.filename, "success": False, "error": "文件超过 10MB"}

        # 上传 MinIO
        try:
            file_id, oss_url, file_hash = upload_file(content, file.filename)
        except Exception as e:
            return {"filename": file.filename, "success": False, "error": f"上传失败: {e}"}

        # 写临时文件识别
        suffix = Path(file.filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            invoice_info = extract_invoice_info(tmp_path)
        finally:
            os.unlink(tmp_path)

        if "error" in invoice_info:
            return {"filename": file.filename, "success": False, "error": invoice_info["error"]}

        # 重复发票检测
        inv_number = invoice_info.get("发票号码")
        if inv_number and db.query(Invoice).filter(Invoice.invoice_number == inv_number).first():
            return {"filename": file.filename, "success": False,
                    "error": f"发票号 {inv_number} 已存在，请勿重复报销"}

        # 解析日期
        from datetime import date as date_type
        invoice_date = None
        raw_date = invoice_info.get("开票日期")
        if raw_date:
            try:
                invoice_date = date_type.fromisoformat(raw_date)
            except Exception:
                pass

        # 存库
        invoice = Invoice(
            file_id=file_id, oss_url=oss_url, file_hash=file_hash,
            invoice_type=invoice_info.get("发票类型"),
            invoice_number=inv_number,
            vendor=invoice_info.get("供应商名称"),
            invoice_date=invoice_date,
            amount=invoice_info.get("金额（不含税）"),
            tax=invoice_info.get("税额"),
            total=invoice_info.get("价税合计"),
            category=invoice_info.get("费用类别"),
            raw_json=invoice_info,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        validation = validate_expense(invoice_info)
        return {
            "filename": file.filename,
            "success": True,
            "invoice_id": invoice.id,
            "info": invoice_info,
            "validation": validation,
        }

    # 并发识别所有发票
    results = await asyncio.gather(*[process_one(f) for f in files])
    success = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    return {
        "total": len(files),
        "success_count": len(success),
        "failed_count": len(failed),
        "results": results,
    }


@router.get("/{invoice_id}", summary="查询发票详情")
def get_invoice(invoice_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    return invoice
