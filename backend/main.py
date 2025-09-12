# main.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime

# Database setup (SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./pos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    quantity = Column(Integer)
    total_price = Column(Float)
    tax_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Smart POS Backend", version="1.0.0")

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class SaleCreate(BaseModel):
    product_name: str
    quantity: int
    total_price: float
    tax_amount: float

# Endpoints
@app.post("/sales/")
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    db_sale = Sale(**sale.dict())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return {"message": "Sale recorded", "sale": db_sale.id}

@app.get("/reports/daily_sales")
def get_daily_sales(db: Session = Depends(get_db)):
    today = datetime.date.today()
    sales = db.query(Sale).filter(func.date(Sale.created_at) == today).all()
    total_sales = sum([s.total_price for s in sales])
    total_tax = sum([s.tax_amount for s in sales])
    return {
        "date": str(today),
        "total_sales": total_sales,
        "total_tax": total_tax,
        "transactions": len(sales)
    }

@app.get("/reports/tax_summary")
def get_tax_summary(db: Session = Depends(get_db)):
    tax_summary = db.query(func.sum(Sale.tax_amount)).scalar()
    return {"total_tax_collected": tax_summary or 0}
