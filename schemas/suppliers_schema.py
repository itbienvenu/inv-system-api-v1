from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class SupplierCreate(BaseModel):
    name: str
    contact_person: str
    email: EmailStr
    phone: str
    address: str
    company_website: Optional[str] = None
    status: str  # 'active' or 'inactive'

class SupplierOut(SupplierCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupplierUpdate(BaseModel):
    name: Optional[str]
    contact_person: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    address: Optional[str]
    company_website: Optional[str]
    status: Optional[str]

    class Config:
        from_attributes = True