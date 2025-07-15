from enum import Enum
from pydantic import BaseModel, UUID4, Field, EmailStr
from typing import List, Optional
from datetime import datetime, UTC
from uuid import UUID, uuid4


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return None

class PaymentMethod(CaseInsensitiveEnum):
    CASH = "cash"
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"


class ProductSold(BaseModel):
    product_id: UUID
    quantity_sold: int = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    discount: float = Field(0.0, ge=0)


class SaleInput(BaseModel):
    buyer_name: str = Field(..., min_length=1, max_length=100)
    buyer_phone: str = Field(..., min_length=6, max_length=20)
    buyer_email: Optional[EmailStr] = None
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    products: List[ProductSold] = Field(..., min_items=1)
    notes: Optional[str] = None
    taxes: float = Field(0.0, ge=0)
    total_discount: float = Field(0.0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    sold_at: Optional[datetime] = None


# SaleOut scheme

class ProductSoldOut(BaseModel):
    product_id: UUID
    product_name: str
    quantity_sold: int
    selling_price: float
    cost_price: Optional[float] = None
    discount: float

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: UUID4
    buyer_name: str
    buyer_phone: str
    buyer_email: Optional[EmailStr] = None

    payment_method: str
    payment_reference: Optional[str]
    currency: str

    subtotal: float
    total_discount: float
    taxes: float
    total: float

    status: str
    notes: Optional[str]

    sold_by: UUID4
    sold_at: datetime
    updated_at: Optional[datetime] = None

    products: List[ProductSoldOut]

    class Config:
        from_attributes = True