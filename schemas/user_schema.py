from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from typing import Optional, List
from enum import Enum
from datetime import datetime, timedelta, UTC
class Roles(str, Enum):
    admin = "admin"
    executive = "exectutive"
    user = "user"

class LoginInput(BaseModel):
    email: EmailStr
    password: str


class RegisterInput(BaseModel):
    id: Optional[UUID] = uuid4()
    names: str
    email: EmailStr
    phone: int
    password: str
    role: List[Roles]

class UpdateInput(BaseModel):
    names: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[int]
    password: Optional[str]


class Users(BaseModel):
    id: Optional[UUID] = uuid4()
    names: str
    email: EmailStr
    phone: int
    password: str
    role: List[Roles]
    created_at: datetime = Field(default_factory=datetime.now(UTC))


    