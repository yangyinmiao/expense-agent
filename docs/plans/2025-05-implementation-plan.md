# 财务报销 Agent — 完整系统开发计划

> **目标：** 按 Phase 2 → Phase 3 顺序，从 MVP Streamlit 演进为生产级全栈系统
>
> **架构：** FastAPI 后端 + PostgreSQL + Redis + MinIO + Streamlit 前端
>
> **原则：** 每个任务独立可运行，完成一个提交一次，不跳步

---

## 目录结构目标

```
expense-agent/
├── code/
│   ├── app.py                  # Streamlit 前端入口
│   ├── core/                   # 核心业务逻辑（已有）
│   │   ├── extractor.py
│   │   └── validator.py
│   ├── config/                 # 配置（已有）
│   │   └── settings.py
│   ├── api/                    # FastAPI 后端（新增）
│   │   ├── main.py             # FastAPI app 入口
│   │   ├── routers/            # 路由分模块
│   │   │   ├── auth.py         # 登录/注册
│   │   │   ├── invoices.py     # 发票上传/识别
│   │   │   ├── claims.py       # 报销申请
│   │   │   └── admin.py        # 管理员接口
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   │   ├── user.py
│   │   │   ├── invoice.py
│   │   │   ├── claim.py
│   │   │   └── rule.py
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   │   ├── user.py
│   │   │   ├── invoice.py
│   │   │   └── claim.py
│   │   ├── services/           # 业务服务层
│   │   │   ├── auth_service.py
│   │   │   ├── storage_service.py  # MinIO 文件上传
│   │   │   └── notify_service.py   # 通知
│   │   ├── tasks/              # Celery 异步任务
│   │   │   └── ocr_task.py
│   │   └── db.py               # 数据库连接
├── docs/
│   ├── DESIGN.md
│   └── plans/
│       └── 2025-05-implementation-plan.md  # 本文件
└── deploy/
    └── docker-compose.yml      # 已有
```

---

## Phase 2：后端基础设施

### Task 1：安装新依赖

**目标：** 装好后端所需的全部依赖包

**执行：**
```bash
cd ~/Documents/Development/PersonalProjects/expense-agent
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy alembic asyncpg psycopg2-binary \
    celery redis minio python-jose[cryptography] passlib[bcrypt] \
    python-multipart aiofiles -i https://pypi.tuna.tsinghua.edu.cn/simple
pip freeze > requirements.txt
```

**验证：**
```bash
python -c "import fastapi, sqlalchemy, celery, minio; print('ok')"
```

**提交：**
```bash
git add requirements.txt && git commit -m "chore: 更新依赖，添加FastAPI/SQLAlchemy/Celery/MinIO"
```

---

### Task 2：启动基础服务

**目标：** 用 docker-compose 启动 PostgreSQL + Redis + MinIO

**执行：**
```bash
cd deploy
cp .env.deploy.example .env
docker-compose up -d
docker-compose ps   # 确认三个服务都是 Up 状态
```

**验证：**
```bash
# PostgreSQL
psql -h localhost -U expense -d expense_agent -c "SELECT 1;"
# Redis
redis-cli ping   # 返回 PONG
# MinIO 控制台
open http://localhost:9001  # admin/minioadmin 登录
```

---

### Task 3：数据库连接与基础配置

**目标：** 建立 SQLAlchemy 数据库连接，更新 settings

**文件：** `code/api/db.py`（新建）、`code/config/settings.py`（修改）

**code/api/db.py：**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**在 settings.py 补充（已有占位符，填实际值）：**
```python
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://expense:changeme@localhost:5432/expense_agent"
)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
```

**验证：**
```bash
cd code && python -c "from api.db import engine; print(engine.connect())"
```

**提交：**
```bash
git add code/api/db.py code/config/settings.py && git commit -m "feat: 数据库连接配置"
```

---

### Task 4：数据模型 — User

**目标：** 创建用户数据模型

**文件：** `code/api/models/user.py`（新建）

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from api.db import Base

class UserRole(str, enum.Enum):
    employee = "employee"    # 员工
    manager = "manager"      # 主管
    finance = "finance"      # 财务
    admin = "admin"          # 管理员

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    department = Column(String(50))
    role = Column(Enum(UserRole), default=UserRole.employee)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**提交：**
```bash
git add code/api/models/ && git commit -m "feat: User 数据模型"
```

---

### Task 5：数据模型 — Invoice / Claim / Rule

**目标：** 创建发票、报销申请、规则数据模型

**文件：** `code/api/models/invoice.py`

```python
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON
from sqlalchemy.sql import func
from api.db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(100), unique=True, index=True)  # OSS 文件名
    oss_url = Column(String(500))
    invoice_type = Column(String(50))
    invoice_number = Column(String(100), index=True)        # 用于重复检测
    vendor = Column(String(200))
    invoice_date = Column(Date)
    amount = Column(Float)       # 不含税金额
    tax = Column(Float)
    total = Column(Float)        # 价税合计
    category = Column(String(50))
    raw_json = Column(JSON)      # GPT 原始返回
    file_hash = Column(String(64))  # MD5，防篡改
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**文件：** `code/api/models/claim.py`

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from api.db import Base

class ClaimStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    manager_approved = "manager_approved"
    finance_approved = "finance_approved"
    rejected = "rejected"
    paid = "paid"

class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(Text)
    status = Column(Enum(ClaimStatus), default=ClaimStatus.draft)
    submitted_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    invoice = relationship("Invoice")
    approvals = relationship("ApprovalRecord", back_populates="claim")

class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("expense_claims.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20))  # approved / rejected
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    claim = relationship("ExpenseClaim", back_populates="approvals")
    approver = relationship("User")
```

**文件：** `code/api/models/rule.py`

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from api.db import Base

class ExpenseRule(Base):
    __tablename__ = "expense_rules"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), unique=True, nullable=False)
    max_amount = Column(Float, nullable=False)
    description = Column(String(200))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))
```

**提交：**
```bash
git add code/api/models/ && git commit -m "feat: Invoice/Claim/Rule 数据模型"
```

---

### Task 6：Alembic 数据库迁移

**目标：** 用 Alembic 自动建表

**执行：**
```bash
cd code
alembic init migrations
# 修改 alembic.ini：sqlalchemy.url = postgresql://expense:changeme@localhost:5432/expense_agent
# 修改 migrations/env.py，导入所有 models
alembic revision --autogenerate -m "初始化表结构"
alembic upgrade head
```

**验证：**
```bash
psql -h localhost -U expense -d expense_agent -c "\dt"
# 应显示 users, invoices, expense_claims, approval_records, expense_rules
```

**提交：**
```bash
git add migrations/ alembic.ini && git commit -m "feat: Alembic 初始化表结构"
```

---

### Task 7：用户认证 — 注册/登录接口

**目标：** 实现 JWT 登录，返回 access_token

**文件：** `code/api/routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from api.db import get_db
from api.models.user import User
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["认证"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm="HS256")

@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register")
def register(name: str, email: str, password: str, department: str = "",
             db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="邮箱已注册")
    user = User(name=name, email=email, department=department,
                hashed_password=pwd_context.hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email}
```

**验证：**
```bash
# 启动服务后测试
curl -X POST http://localhost:8000/auth/register \
  -d "name=测试员工&email=test@company.com&password=123456"
curl -X POST http://localhost:8000/auth/login \
  -d "username=test@company.com&password=123456"
```

**提交：**
```bash
git add code/api/routers/auth.py && git commit -m "feat: 用户注册/登录接口"
```

---

### Task 8：文件存储服务（MinIO）

**目标：** 发票文件上传到 MinIO，返回访问 URL

**文件：** `code/api/services/storage_service.py`

```python
import hashlib
import uuid
from minio import Minio
from minio.error import S3Error
from config.settings import settings

client = Minio(
    "localhost:9000",
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=False,
)
BUCKET = "invoices"

def ensure_bucket():
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)

def upload_file(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """上传文件，返回 (file_id, url)"""
    ensure_bucket()
    file_id = f"{uuid.uuid4().hex}_{filename}"
    file_hash = hashlib.md5(file_bytes).hexdigest()

    import io
    client.put_object(BUCKET, file_id, io.BytesIO(file_bytes), len(file_bytes))

    # 生成7天有效的临时访问URL
    from datetime import timedelta
    url = client.presigned_get_object(BUCKET, file_id, expires=timedelta(days=7))
    return file_id, url, file_hash
```

**验证：**
```bash
python -c "
from api.services.storage_service import upload_file
fid, url, h = upload_file(b'test content', 'test.jpg')
print(fid, url)
"
```

**提交：**
```bash
git add code/api/services/storage_service.py && git commit -m "feat: MinIO 文件存储服务"
```

---

### Task 9：发票上传识别接口

**目标：** POST /invoices/upload → 上传文件 → 识别 → 存库 → 返回结构化信息

**文件：** `code/api/routers/invoices.py`

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import tempfile, os
from pathlib import Path
from api.db import get_db
from api.models.invoice import Invoice
from api.services.storage_service import upload_file
from core.extractor import extract_invoice_info
from core.validator import validate_expense

router = APIRouter(prefix="/invoices", tags=["发票"])

@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. 读取文件
    content = await file.read()

    # 2. 上传到 MinIO
    file_id, oss_url, file_hash = upload_file(content, file.filename)

    # 3. 保存临时文件用于识别
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 4. GPT-4o 识别
        invoice_info = extract_invoice_info(tmp_path)
    finally:
        os.unlink(tmp_path)

    if "error" in invoice_info:
        raise HTTPException(status_code=422, detail=f"识别失败: {invoice_info['error']}")

    # 5. 重复发票检测
    inv_number = invoice_info.get("发票号码")
    if inv_number:
        existing = db.query(Invoice).filter(Invoice.invoice_number == inv_number).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"发票 {inv_number} 已存在，请勿重复报销")

    # 6. 存库
    invoice = Invoice(
        file_id=file_id, oss_url=oss_url, file_hash=file_hash,
        invoice_type=invoice_info.get("发票类型"),
        invoice_number=inv_number,
        vendor=invoice_info.get("供应商名称"),
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

    return {"invoice_id": invoice.id, "info": invoice_info, "validation": validation}
```

**验证：**
```bash
curl -X POST http://localhost:8000/invoices/upload \
  -F "file=@/path/to/test_invoice.jpg"
```

**提交：**
```bash
git add code/api/routers/invoices.py && git commit -m "feat: 发票上传识别接口（含重复检测）"
```

---

### Task 10：报销申请接口（CRUD）

**目标：** 创建/查询/提交报销申请

**文件：** `code/api/routers/claims.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from api.db import get_db
from api.models.claim import ExpenseClaim, ClaimStatus

router = APIRouter(prefix="/claims", tags=["报销申请"])

@router.post("/")
def create_claim(user_id: int, invoice_id: int, description: str = "",
                 db: Session = Depends(get_db)):
    """创建报销申请（草稿状态）"""
    claim = ExpenseClaim(user_id=user_id, invoice_id=invoice_id,
                         description=description, status=ClaimStatus.draft)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return {"claim_id": claim.id, "status": claim.status}

@router.post("/{claim_id}/submit")
def submit_claim(claim_id: int, db: Session = Depends(get_db)):
    """提交审批"""
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    if claim.status != ClaimStatus.draft:
        raise HTTPException(status_code=400, detail="只有草稿状态可以提交")
    claim.status = ClaimStatus.pending
    claim.submitted_at = datetime.utcnow()
    db.commit()
    return {"claim_id": claim.id, "status": claim.status}

@router.get("/{claim_id}")
def get_claim(claim_id: int, db: Session = Depends(get_db)):
    """查询申请详情"""
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    return claim

@router.get("/user/{user_id}")
def list_user_claims(user_id: int, db: Session = Depends(get_db)):
    """查询某用户的所有申请"""
    return db.query(ExpenseClaim).filter(ExpenseClaim.user_id == user_id).all()
```

**提交：**
```bash
git add code/api/routers/claims.py && git commit -m "feat: 报销申请 CRUD 接口"
```

---

### Task 11：FastAPI 主入口

**目标：** 组装所有路由，启动服务

**文件：** `code/api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, invoices, claims

app = FastAPI(title="财务报销 Agent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(claims.router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**启动：**
```bash
cd code && uvicorn api.main:app --reload --port 8000
# 访问 http://localhost:8000/docs 查看自动生成的 API 文档
```

**提交：**
```bash
git add code/api/main.py && git commit -m "feat: FastAPI 主入口，整合所有路由"
```

---

## Phase 3：审批流 + 异常检测

### Task 12：审批接口

**目标：** 主管/财务审批通过或驳回

**文件：** `code/api/routers/claims.py`（追加）

```python
@router.post("/{claim_id}/approve")
def approve_claim(claim_id: int, approver_id: int, comment: str = "",
                  db: Session = Depends(get_db)):
    """审批通过"""
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")

    # 按当前状态推进
    next_status = {
        ClaimStatus.pending: ClaimStatus.manager_approved,
        ClaimStatus.manager_approved: ClaimStatus.finance_approved,
    }.get(claim.status)

    if not next_status:
        raise HTTPException(status_code=400, detail=f"当前状态 {claim.status} 无法审批")

    claim.status = next_status
    record = ApprovalRecord(claim_id=claim_id, approver_id=approver_id,
                            action="approved", comment=comment)
    db.add(record)
    db.commit()
    return {"claim_id": claim_id, "status": claim.status}

@router.post("/{claim_id}/reject")
def reject_claim(claim_id: int, approver_id: int, comment: str,
                 db: Session = Depends(get_db)):
    """驳回"""
    claim = db.query(ExpenseClaim).filter(ExpenseClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="申请不存在")
    claim.status = ClaimStatus.rejected
    record = ApprovalRecord(claim_id=claim_id, approver_id=approver_id,
                            action="rejected", comment=comment)
    db.add(record)
    db.commit()
    return {"claim_id": claim_id, "status": "rejected", "reason": comment}
```

**提交：**
```bash
git commit -am "feat: 审批通过/驳回接口"
```

---

### Task 13：异常检测增强

**目标：** 金额预警（单月同类超限）+ 发票真实性 hash 验证

**文件：** `code/api/services/anomaly_service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from api.models.invoice import Invoice
from api.models.claim import ExpenseClaim, ClaimStatus

MONTHLY_LIMITS = {
    "餐饮": 3000,
    "交通": 10000,
    "住宿": 5000,
    "办公用品": 5000,
}

def check_monthly_anomaly(user_id: int, category: str,
                          amount: float, db: Session) -> dict:
    """检查单月同类别累计是否超限"""
    now = datetime.utcnow()
    monthly_total = db.query(func.sum(Invoice.total))\
        .join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id)\
        .filter(
            ExpenseClaim.user_id == user_id,
            Invoice.category == category,
            ExpenseClaim.status.notin_([ClaimStatus.rejected]),
            extract("year", ExpenseClaim.submitted_at) == now.year,
            extract("month", ExpenseClaim.submitted_at) == now.month,
        ).scalar() or 0

    limit = MONTHLY_LIMITS.get(category, 3000)
    after_total = monthly_total + amount

    return {
        "月度已报销": monthly_total,
        "本次金额": amount,
        "月度上限": limit,
        "超限预警": after_total > limit,
        "超出金额": max(0, after_total - limit),
    }
```

**提交：**
```bash
git add code/api/services/anomaly_service.py && git commit -m "feat: 月度异常检测服务"
```

---

### Task 14：统计报表接口

**目标：** 财务端查询月度/部门报销统计

**文件：** `code/api/routers/admin.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from api.db import get_db
from api.models.invoice import Invoice
from api.models.claim import ExpenseClaim, ClaimStatus
from api.models.user import User

router = APIRouter(prefix="/admin", tags=["管理员"])

@router.get("/stats/monthly")
def monthly_stats(year: int, month: int, db: Session = Depends(get_db)):
    """月度报销统计（按类别）"""
    results = db.query(
        Invoice.category,
        func.count(ExpenseClaim.id).label("申请数"),
        func.sum(Invoice.total).label("总金额"),
    ).join(ExpenseClaim, ExpenseClaim.invoice_id == Invoice.id)\
     .filter(
         ExpenseClaim.status == ClaimStatus.finance_approved,
         extract("year", ExpenseClaim.submitted_at) == year,
         extract("month", ExpenseClaim.submitted_at) == month,
     ).group_by(Invoice.category).all()

    return [{"类别": r[0], "申请数": r[1], "总金额": r[2]} for r in results]

@router.get("/stats/department")
def department_stats(year: int, month: int, db: Session = Depends(get_db)):
    """月度报销统计（按部门）"""
    results = db.query(
        User.department,
        func.count(ExpenseClaim.id).label("申请数"),
        func.sum(Invoice.total).label("总金额"),
    ).join(ExpenseClaim, ExpenseClaim.user_id == User.id)\
     .join(Invoice, Invoice.id == ExpenseClaim.invoice_id)\
     .filter(
         ExpenseClaim.status == ClaimStatus.finance_approved,
         extract("year", ExpenseClaim.submitted_at) == year,
         extract("month", ExpenseClaim.submitted_at) == month,
     ).group_by(User.department).all()

    return [{"部门": r[0], "申请数": r[1], "总金额": r[2]} for r in results]
```

**提交：**
```bash
git add code/api/routers/admin.py && git commit -m "feat: 月度/部门统计报表接口"
```

---

### Task 15：Streamlit 前端对接后端 API

**目标：** 把 app.py 从直接调 core/ 改为调用 FastAPI 接口

**文件：** `code/app.py`（重构关键部分）

```python
import requests

API_BASE = "http://localhost:8000"

# 上传发票
def api_upload_invoice(file_bytes, filename):
    resp = requests.post(
        f"{API_BASE}/invoices/upload",
        files={"file": (filename, file_bytes)},
    )
    return resp.json()

# 创建并提交报销申请
def api_submit_claim(invoice_id, description, user_id=1):
    claim = requests.post(f"{API_BASE}/claims/",
        params={"user_id": user_id, "invoice_id": invoice_id,
                "description": description}).json()
    requests.post(f"{API_BASE}/claims/{claim['claim_id']}/submit")
    return claim
```

**提交：**
```bash
git commit -am "feat: Streamlit 前端对接 FastAPI 后端"
```

---

## 开发顺序总结

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| **Phase 2** | Task 1~3：环境搭建 | 0.5天 |
| | Task 4~6：数据模型 + 建表 | 1天 |
| | Task 7~8：认证 + 存储 | 1天 |
| | Task 9~11：核心接口 + 启动 | 1天 |
| **Phase 3** | Task 12：审批流 | 0.5天 |
| | Task 13：异常检测 | 0.5天 |
| | Task 14：统计报表 | 0.5天 |
| | Task 15：前端对接 | 0.5天 |
| **合计** | | **~6天** |

---

## 每日启动命令

```bash
# 1. 启动基础服务
cd ~/Documents/Development/PersonalProjects/expense-agent/deploy
docker-compose up -d

# 2. 激活虚拟环境
cd ..
source venv/bin/activate

# 3. 启动 FastAPI
cd code && uvicorn api.main:app --reload --port 8000

# 4. 另开终端启动 Streamlit
streamlit run code/app.py
```
