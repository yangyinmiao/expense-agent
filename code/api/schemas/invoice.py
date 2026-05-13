from pydantic import BaseModel
from typing import Optional, Any


class InvoiceOut(BaseModel):
    id: int
    file_id: str
    oss_url: Optional[str]
    invoice_type: Optional[str]
    invoice_number: Optional[str]
    vendor: Optional[str]
    amount: Optional[float]
    tax: Optional[float]
    total: Optional[float]
    category: Optional[str]
    invoice_date: Optional[str]
    raw_json: Optional[Any]

    class Config:
        from_attributes = True


class InvoiceUploadOut(BaseModel):
    invoice_id: int
    info: dict
    validation: dict
