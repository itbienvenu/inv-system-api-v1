from enum import Enum
from pydantic import BaseModel, UUID4, Field, EmailStr
from typing import List, Optional
from datetime import datetime, UTC
from uuid import UUID, uuid4

class PaymentMethod(str, Enum):
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
