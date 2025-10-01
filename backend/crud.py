# crud.py
from sqlalchemy.orm import Session
from typing import List
import models
import schemas

# Custom Exceptions for business logic
class ProductNotFoundException(Exception):
    pass
class InsufficientStockException(Exception):
    pass

# --- Product CRUD ---

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_name(db: Session, name: str):
    return db.query(models.Product).filter(models.Product.name == name).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        raise ProductNotFoundException(f"Product with id {product_id} not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if not db_product:
        raise ProductNotFoundException(f"Product with id {product_id} not found")
    db.delete(db_product)
    db.commit()
    return db_product

# --- Sale CRUD ---

TAX_RATE = 0.16 # 16% VAT

def create_sale(
    db: Session, 
    sale_items: List[schemas.SaleItemCreate],
    discount_amount: float,
    zra_response: dict = None
):
    # Use a transaction to ensure atomicity
    try:
        subtotal = 0
        processed_items = []

        for item in sale_items:
            # Lock the product row for update to prevent race conditions
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if not product:
                raise ProductNotFoundException(f"Product with id {item.product_id} not found")
            if product.stock_quantity < item.quantity:
                raise InsufficientStockException(f"Not enough stock for {product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}")
            
            product.stock_quantity -= item.quantity
            subtotal += product.price * item.quantity
            processed_items.append({"product_id": item.product_id, "quantity": item.quantity, "price_at_sale": product.price})

        tax_amount = (subtotal - discount_amount) * TAX_RATE
        total_amount = (subtotal - discount_amount) + tax_amount

        db_sale = models.Sale(
            total_amount=total_amount, 
            tax_amount=tax_amount, 
            discount_amount=discount_amount
        )
        if zra_response:
            db_sale.zra_invoice_id = zra_response.get("zra_invoice_id")
            db_sale.zra_response_log = str(zra_response)
            db_sale.zra_sync_status = models.SyncStatus.SYNCED

        db.add(db_sale)
        db.flush() # Use flush to get the db_sale.id before commit

        for p_item in processed_items:
            db_item = models.SaleItem(sale_id=db_sale.id, **p_item)
            db.add(db_item)
        
        db.commit()
        db.refresh(db_sale)
        return db_sale
    except Exception as e:
        db.rollback() # Rollback any changes if validation fails
        raise e

def get_sale(db: Session, sale_id: int):
    return db.query(models.Sale).filter(models.Sale.id == sale_id).first()

def get_sales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sale).offset(skip).limit(limit).all()

# --- Reporting ---
from sqlalchemy import func
from datetime import date

def get_sales_summary_by_day(db: Session, day: date):
    """
    Generates a sales summary for a specific day.
    """
    summary = db.query(
        func.sum(models.Sale.total_amount).label("total_sales"),
        func.sum(models.Sale.tax_amount).label("total_tax"),
        func.count(models.Sale.id).label("number_of_transactions")
    ).filter(func.date(models.Sale.created_at) == day).first()
    
    return summary