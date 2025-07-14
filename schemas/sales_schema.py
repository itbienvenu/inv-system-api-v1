from enum import Enum
from pydantic import BaseModel, UUID4, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"

class ProductSold(BaseModel):
    product_id: UUID4
    quantity_sold: int = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    cost_price: Optional[float] = None  # For profit calculation
    discount: float = Field(0.0, ge=0)  # Discount applied to this product

class SaleInput(BaseModel):
    sale_id: UUID4 = Field(default_factory=uuid4)
    buyer_name: str = Field(..., min_length=1, max_length=100)
    buyer_phone: str = Field(..., min_length=6, max_length=20)
    buyer_email: Optional[EmailStr] = None
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None  # For card/transfer receipts
    sold_by: UUID4
    sold_at: datetime = Field(default_factory=datetime.now)
    location_id: UUID4  # For multi-location businesses
    device_id: Optional[str] = None  # Which POS device was used
    products: List[ProductSold] = Field(..., min_items=1)
    notes: Optional[str] = None
    taxes: float = Field(0.0, ge=0)
    total_discount: float = Field(0.0, ge=0)
    subtotal: float = Field(..., gt=0)
    total: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    is_return: bool = False  # For return transactions
    original_sale_id: Optional[UUID4] = None  # For returns/linked transactions
    status: str = Field("completed", pattern="^(completed|pending|refunded|partially_refunded)$")