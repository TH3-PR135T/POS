# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime
from typing import List

import crud
import models
import schemas
from database import SessionLocal, engine, Base
from mock_zra_server import app as mock_zra_app

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart POS API",
    description="API for the Point of Sale system with E-Invoicing integration.",
    version="1.0.0"
)

# This import is moved down to avoid circular dependency issues if client also imports from main
from zra_integration.client import ZRAClient


# --- ZRA Client Setup ---
# The mock server is now part of this app, so we don't need a full URL.
# We will use an internal client to talk to it.
# However, for simplicity and to keep the client code unchanged, we'll point to our own server.
# In a production app, you would use a real URL and manage this with environment variables.
ZRA_API_BASE_URL = "http://127.0.0.1:8000/mock_zra" # URL points to the mounted mock app
ZRA_API_KEY = "test_api_key"
zra_client = ZRAClient(base_url=ZRA_API_BASE_URL, api_key=ZRA_API_KEY)

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Product Endpoints ---

@app.post("/products/", response_model=schemas.Product, tags=["Products"])
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = crud.get_product_by_name(db, name=product.name)
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this name already exists")
    return crud.create_product(db=db, product=product)

@app.get("/products/", response_model=List[schemas.Product], tags=["Products"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = crud.get_products(db, skip=skip, limit=limit)
    return products

@app.get("/products/{product_id}", response_model=schemas.Product, tags=["Products"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.put("/products/{product_id}", response_model=schemas.Product, tags=["Products"])
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    try:
        return crud.update_product(db, product_id=product_id, product_update=product)
    except crud.ProductNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/products/{product_id}", response_model=schemas.Product, tags=["Products"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        return crud.delete_product(db, product_id=product_id)
    except crud.ProductNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

# --- Sale & Report Endpoints ---

TAX_RATE = 0.16 # 16% VAT

@app.post("/sales/", response_model=schemas.Sale, tags=["Sales"])
def create_sale(sale: schemas.SaleCreate, db: Session = Depends(get_db)):
    # To submit to ZRA before saving, we must pre-calculate the totals and fetch product info.
    # This duplicates some logic from the CRUD function, which is a trade-off.
    # The CRUD function's atomic transaction remains the source of truth for the DB.
    subtotal = 0
    zra_items = []
    for item in sale.items:
        product = crud.get_product(db, item.product_id)
        if not product:
            # This check is duplicated but necessary for ZRA payload creation.
            raise HTTPException(status_code=404, detail=f"Product with id {item.product_id} not found")
        subtotal += product.price * item.quantity
        zra_items.append(schemas.ZRAInvoiceItem(item_name=product.name, quantity=item.quantity, price=product.price))

    tax_amount = (subtotal - sale.discount_amount) * TAX_RATE
    total_amount = (subtotal - sale.discount_amount) + tax_amount

    # --- ZRA API Submission Logic ---
    zra_response = None
    # A real transaction ID can only be known after the sale is created.
    # This is a classic challenge. A common pattern is to use a temporary or pre-generated UUID.
    temp_transaction_id = f"SALE-{datetime.datetime.utcnow().timestamp()}"
    invoice_payload = schemas.ZRAInvoiceSubmission(
        transaction_id=temp_transaction_id,
        total_amount=total_amount,
        tax_amount=tax_amount,
        items=zra_items
    )

    try:
        print("Submitting invoice to ZRA...")
        zra_response = zra_client.submit_invoice(invoice_payload)
        print(f"ZRA submission successful: {zra_response}")
    except Exception as e:
        # For now, we just log the error. The sale will be saved with PENDING status.
        # The offline queue/retry mechanism will handle this later.
        print(f"ZRA submission failed: {e}")

    try:
        # The CRUD function now takes the sale items and discount directly.
        # It should handle all database logic, including stock checks, atomically.
        created_sale = crud.create_sale(db=db, sale_items=sale.items, discount_amount=sale.discount_amount, zra_response=zra_response)
        return created_sale
    except crud.ProductNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except crud.InsufficientStockException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/sales/{sale_id}", response_model=schemas.Sale, tags=["Sales"])
def read_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = crud.get_sale(db, sale_id=sale_id)
    if db_sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    return db_sale

@app.get("/sales/", response_model=List[schemas.Sale], tags=["Sales"])
def read_sales(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sales = crud.get_sales(db, skip=skip, limit=limit)
    return sales

class DailySummaryResponse(schemas.BaseModel):
    date: datetime.date
    total_sales: float
    total_tax: float
    number_of_transactions: int

@app.get("/reports/daily_summary", response_model=DailySummaryResponse, tags=["Reports"])
def get_daily_summary(day: datetime.date, db: Session = Depends(get_db)):
    today = datetime.date.today()
    summary = crud.get_sales_summary_by_day(db, day=day)
    
    if not summary or summary.total_sales is None:
        return DailySummaryResponse(
            date=day, total_sales=0, total_tax=0, number_of_transactions=0
        )

    return DailySummaryResponse(date=day, **summary._asdict())

@app.get("/reports/tax_summary", tags=["Reports"])
def get_tax_summary(db: Session = Depends(get_db)):
    tax_summary = db.query(func.sum(models.Sale.tax_amount)).scalar()
    return {"total_tax_collected": tax_summary or 0.0}

# Mount the mock ZRA server onto the main application
app.mount("/mock_zra", mock_zra_app)
