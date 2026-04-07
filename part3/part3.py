from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from database import get_db
from models import Product, Inventory, Warehouse, Supplier, ProductSupplier, OrderItem

router = APIRouter()

# --- 1. Pydantic Response Schemas ---

class SupplierResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    contact_email: Optional[EmailStr] = None

class StockAlert(BaseModel):
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    current_stock: int
    threshold: int
    days_until_stockout: int
    supplier: SupplierResponse

class LowStockResponse(BaseModel):
    alerts: List[StockAlert]
    total_alerts: int

# --- 2. The Logic Implementation ---

@router.get("/api/companies/{company_id}/alerts/low-stock", response_model=LowStockResponse)
def get_low_stock_alerts(company_id: int, db: Session = Depends(get_db)):
    """
    Business Logic: 
    - Identifies products below threshold.
    - Filters only for products with movement (sales) in the last 30 days.
    - Calculates runway based on velocity.
    """
    alerts = []
    RECENT_DAYS = 30
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)

    try:
        # Optimized Query: Eager load inventory and warehouses to avoid multiple DB hits
        # We also filter by company_id at the top level
        records = db.query(Product)\
            .join(Inventory, Product.id == Inventory.product_id)\
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)\
            .options(
                joinedload(Product.inventory).joinedload(Inventory.warehouse)
            )\
            .filter(Warehouse.company_id == company_id)\
            .all()

        for product in records:
            # Step 1: Calculate velocity (sales volume)
            total_sold = db.query(func.sum(OrderItem.quantity))\
                .filter(OrderItem.product_id == product.id)\
                .filter(OrderItem.created_at >= cutoff_date)\
                .scalar() or 0

            # Rule: If it's not selling, we don't need an urgent alert
            if total_sold <= 0:
                continue

            avg_daily_sales = total_sold / RECENT_DAYS

            for inv in product.inventory:
                threshold = getattr(product, "low_stock_threshold", 10)

                if inv.quantity <= threshold:
                    # Step 2: Calculate Runway
                    # Potential Edge Case: avg_daily_sales is > 0 but very small
                    days_until_stockout = inv.quantity / avg_daily_sales

                    # Step 3: Get Primary Supplier
                    supplier_record = db.query(Supplier)\
                        .join(ProductSupplier, Supplier.id == ProductSupplier.supplier_id)\
                        .filter(ProductSupplier.product_id == product.id)\
                        .first()

                    alerts.append(StockAlert(
                        product_id=product.id,
                        product_name=product.name,
                        sku=product.sku,
                        warehouse_id=inv.warehouse_id,
                        warehouse_name=inv.warehouse.name,
                        current_stock=inv.quantity,
                        threshold=threshold,
                        days_until_stockout=int(days_until_stockout),
                        supplier=SupplierResponse(
                            id=supplier_record.id if supplier_record else None,
                            name=supplier_record.name if supplier_record else None,
                            contact_email=supplier_record.contact_email if supplier_record else None
                        )
                    ))

        return LowStockResponse(alerts=alerts, total_alerts=len(alerts))

    except Exception as e:
        # Log error here (e.g., logging.error(e))
        raise HTTPException(status_code=500, detail="Error generating stock alerts")