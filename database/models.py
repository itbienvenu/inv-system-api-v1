from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
import uuid
from uuid import uuid4
from datetime import datetime, timedelta, UTC
from enum import Enum as PyEnum

Base = declarative_base()

# Enums for database
class PaymentMethodDB(PyEnum):
    CASH = "cash"
    CARD = "card"
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"

class SaleStatusDB(PyEnum):
    COMPLETED = "completed"
    PENDING = "pending"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    names = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(Integer, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("email", name="unique_user_email"),
    )

class Product(Base):
    __tablename__ = "products"  # Changed from "product" to "products" for consistency
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_name = Column(String, nullable=False)
    selling_price = Column(Float, nullable=False)
    buying_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    front_image = Column(String, nullable=False)
    back_image = Column(String, nullable=False)
    description = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)
    unit = Column(String, nullable=False)
    low_stock_alert = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_modified = Column(DateTime, default=datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("sku", name="unique_product_sku"),
    )

class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    original_sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    device_id = Column(String, nullable=True)
    
    buyer_name = Column(String(100), nullable=False)  # Changed from nullable=True
    buyer_phone = Column(String(20), nullable=False)  # Changed from nullable=True
    buyer_email = Column(String, nullable=True)
    
    payment_method = Column(ENUM(PaymentMethodDB), nullable=False)  # Changed from String
    payment_reference = Column(String, nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    notes = Column(String, nullable=True)
    
    subtotal = Column(Float, nullable=False)
    total_discount = Column(Float, default=0.0, nullable=False)
    taxes = Column(Float, default=0.0, nullable=False)
    total = Column(Float, nullable=False)  # Renamed from total_price for consistency
    
    status = Column(ENUM(SaleStatusDB), default="completed", nullable=False)
    is_return = Column(Boolean, default=False, nullable=False)
    
    sold_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sold_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ProductSold(Base):
    __tablename__ = "products_sold"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    product_name = Column(String, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    selling_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=True)  # Added for profit calculation
    discount = Column(Float, default=0.0, nullable=False)  # Added for per-product discounts

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    is_active = Column(Boolean, default=True, nullable=False)