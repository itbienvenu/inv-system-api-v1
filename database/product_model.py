from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime, timedelta, UTC

# Base = declarative_base()



__table_args__ = (
        UniqueConstraint("sku", name="unique_product_sku"),
    )