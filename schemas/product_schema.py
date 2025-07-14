from pydantic import EmailStr, BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, UTC
from enum import Enum


class ProductImage(BaseModel):
    front_image: str
    other_images: List[str]


class ProductInput(BaseModel):
    id: Optional[UUID] = uuid4()
    created_by: UUID
    product_name: str
    selling_price: float
    buying_price: float
    quantity: int
    category: str
    brand: Optional[str] = None
    image: ProductImage
    description: Optional[str] = None
    sku: Optional[str] = None
    unit: Optional[str] = "pcs"
    low_stock_alert: Optional[int] = 10
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        orm_mode = True

class ProductOut(BaseModel):
    id: UUID
    created_by: UUID
    product_name: str
    selling_price: float
    buying_price: float
    quantity: int
    category: str
    brand: str
    front_image: str
    back_image: List[str]
    description: str
    sku: str
    unit: str
    low_stock_alert: int
    created_at: datetime
    last_modified: datetime

    class Config:
        orm_mode = True

class ProductUpdate(BaseModel):
    product_name: Optional[str]
    selling_price: Optional[float]
    buying_price: Optional[float]
    quantity: Optional[int]
    category: Optional[str]
    brand: Optional[str]
    front_image: Optional[str]
    back_image: Optional[List[str]]
    description: Optional[str]
    sku: Optional[str]
    unit: Optional[str]
    low_stock_alert: Optional[int]
    last_modified: Optional[datetime] = None

    class Config:
        orm_mode = True