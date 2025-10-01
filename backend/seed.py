# backend/seed.py
import sys
import os
import logging
from sqlalchemy.orm import Session

# --- Setup for standalone script execution ---
# Add the project root to the Python path to allow imports from other modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
# --- End Setup ---

from database import SessionLocal, engine
from models import Base, Product, Sale, SaleItem
from schemas import SaleItemCreate
from crud import create_sale, get_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    """
    Populates the database with initial data for products and sales.
    This function is idempotent; it won't re-seed if products already exist.
    """
    db: Session = SessionLocal()

    try:
        # Check if data already exists to prevent re-seeding
        if get_products(db):
            logger.info("Database already contains products. Skipping seeding.")
            return

        logger.info("Seeding products...")
        # --- 1. Create Products ---
        products_to_create = [
            Product(name="Laptop Pro", description="A powerful laptop for all your needs.", price=1250.50, stock_quantity=50),
            Product(name="Smartphone X", description="Latest model with a great camera.", price=800.00, stock_quantity=150),
            Product(name="Wireless Mouse", description="Ergonomic wireless mouse.", price=25.99, stock_quantity=200),
            Product(name="Mechanical Keyboard", description="Mechanical keyboard with RGB.", price=75.00, stock_quantity=100),
            Product(name="4K Monitor", description="27-inch 4K UHD monitor.", price=350.75, stock_quantity=30),
        ]
        db.add_all(products_to_create)
        db.commit()

        # Refresh objects to get their assigned IDs from the database
        for p in products_to_create:
            db.refresh(p)

        logger.info("Products seeded successfully.")

        logger.info("Seeding sales using CRUD function...")
        # --- 2. Create Sales ---
        # This re-uses your existing business logic from crud.py to ensure stock is handled correctly.

        # Sale 1: A laptop and a mouse
        sale1_items = [
            SaleItemCreate(product_id=products_to_create[0].id, quantity=1),  # Laptop Pro
            SaleItemCreate(product_id=products_to_create[2].id, quantity=1),  # Wireless Mouse
        ]
        create_sale(db=db, sale_items=sale1_items, discount_amount=50.0)

        # Sale 2: Two smartphones and a keyboard, no discount
        sale2_items = [
            SaleItemCreate(product_id=products_to_create[1].id, quantity=2),  # Smartphone X
            SaleItemCreate(product_id=products_to_create[3].id, quantity=1),  # Mechanical Keyboard
        ]
        create_sale(db=db, sale_items=sale2_items, discount_amount=0.0)

        logger.info("Sales seeded successfully.")
        logger.info("Database seeding complete!")

    except Exception as e:
        logger.error(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Running database seeder...")
    # This ensures tables are created before seeding
    Base.metadata.create_all(bind=engine)
    seed_data()