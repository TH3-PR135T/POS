# schemas.py
from pydantic import BaseModel
from typing import List, Optional
import datetime

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

# --- Sale Schemas ---
class SaleItemBase(BaseModel):
    product_id: int
    quantity: int

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    id: int
    price_at_sale: float

    class Config:
        from_attributes = True

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    discount_amount: Optional[float] = 0.0

class Sale(BaseModel):
    id: int
    total_amount: float
    tax_amount: float
    discount_amount: float
    created_at: datetime.datetime
    items: List[SaleItem] = []

    class Config:
        from_attributes = True

# --- ZRA Integration Schemas ---

class ZRAInvoiceItem(BaseModel):
    item_name: str
    quantity: float
    price: float

class ZRAInvoiceSubmission(BaseModel):
    transaction_id: str
    total_amount: float
    tax_amount: float
    items: List[ZRAInvoiceItem]