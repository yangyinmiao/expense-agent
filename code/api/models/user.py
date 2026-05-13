from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from api.db import Base


class UserRole(str, enum.Enum):
    employee = "employee"   # 员工
    manager = "manager"     # 主管
    finance = "finance"     # 财务
    admin = "admin"         # 管理员


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    department = Column(String(50), default="")
    role = Column(Enum(UserRole), default=UserRole.employee, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
