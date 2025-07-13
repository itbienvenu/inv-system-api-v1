from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timedelta, UTC


Base = declarative_base()

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
    __tablename__ = "product"
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