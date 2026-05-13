from pydantic import BaseModel, EmailStr
from typing import Optional
from api.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = ""


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
