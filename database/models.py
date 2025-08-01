from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint, Float, Enum as SQLAlchemyEnum
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

    buyer_name = Column(String(100), nullable=False)
    buyer_phone = Column(String(20), nullable=False)
    buyer_email = Column(String, nullable=True)

    payment_method = Column(
    SQLAlchemyEnum(PaymentMethodDB, values_callable=lambda obj: [e.value for e in obj]), 
    nullable=False
)
    payment_reference = Column(String, nullable=True)

    subtotal = Column(Float, nullable=False)  # Backend-calculated
    total_discount = Column(Float, default=0.0, nullable=False)
    taxes = Column(Float, default=0.0, nullable=False)
    total = Column(Float, nullable=False)  # Backend-calculated

    currency = Column(String(3), default="USD", nullable=False)
    status = Column(
    SQLAlchemyEnum(SaleStatusDB, values_callable=lambda obj: [e.value for e in obj]), 
    nullable=False,
    default=SaleStatusDB.COMPLETED.value
)
    notes = Column(String, nullable=True)

    sold_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sold_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProductSold(Base):
    __tablename__ = "products_sold"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    product_name = Column(String, nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    selling_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=True)  # Backend-filled
    discount = Column(Float, default=0.0, nullable=False)


class Location(Base):
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    is_active = Column(Boolean, default=True, nullable=False)

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_person = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    company_website = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))