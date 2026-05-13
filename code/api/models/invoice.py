from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON
from sqlalchemy.sql import func
from api.db import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(200), unique=True, index=True)   # MinIO 文件名
    oss_url = Column(String(1000))
    invoice_type = Column(String(50))
    invoice_number = Column(String(100), index=True)         # 用于重复检测
    vendor = Column(String(200))
    invoice_date = Column(Date)
    amount = Column(Float)        # 不含税金额
    tax = Column(Float)
    total = Column(Float)         # 价税合计
    category = Column(String(50))
    raw_json = Column(JSON)       # GPT 原始返回
    file_hash = Column(String(64))  # MD5，防篡改
    created_at = Column(DateTime(timezone=True), server_default=func.now())
