# models.py
import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from database import Base

class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0)

    sale_items = relationship("SaleItem", back_populates="product")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # ZRA Integration Fields
    zra_invoice_id = Column(String, nullable=True, index=True)
    zra_sync_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    zra_response_log = Column(String, nullable=True)

    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_sale = Column(Float) # Price of the product when the sale was made

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")