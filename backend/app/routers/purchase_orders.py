# purchase_orders.py - All API routes for Purchase Orders
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app import models, schemas

router = APIRouter()


def generate_reference_number(db: Session) -> str:
    year = datetime.now().year
    count = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.reference_no.like(f"PO-{year}-%")
    ).count()
    return f"PO-{year}-{str(count + 1).zfill(4)}"


TAX_RATE = 0.05

def calculate_totals(items: list) -> dict:
    subtotal     = sum(item.line_total for item in items)
    tax_amount   = round(subtotal * TAX_RATE, 2)
    total_amount = round(subtotal + tax_amount, 2)
    return {
        "subtotal"    : round(subtotal, 2),
        "tax_amount"  : tax_amount,
        "total_amount": total_amount
    }


# ─────────────────────────────────────────────
# GET /api/purchase-orders
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.PurchaseOrderResponse])
def get_all_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        pos = db.query(models.PurchaseOrder).offset(skip).limit(limit).all()
        return pos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching purchase orders: {str(e)}"
        )


# ─────────────────────────────────────────────
# GET /api/purchase-orders/{id}
# ─────────────────────────────────────────────
@router.get("/{po_id}", response_model=schemas.PurchaseOrderResponse)
def get_purchase_order(po_id: int, db: Session = Depends(get_db)):
    try:
        po = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.id == po_id
        ).first()

        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order with id {po_id} not found"
            )
        return po
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching purchase order: {str(e)}"
        )


# ─────────────────────────────────────────────
# POST /api/purchase-orders
# ─────────────────────────────────────────────
@router.post("/", response_model=schemas.PurchaseOrderResponse,
             status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_data: schemas.PurchaseOrderCreate,
    db: Session = Depends(get_db)
):
    try:
        # 1. Check vendor exists
        vendor = db.query(models.Vendor).filter(
            models.Vendor.id == po_data.vendor_id
        ).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id {po_data.vendor_id} not found"
            )

        # 2. Validate all products exist
        for item_data in po_data.items:
            product = db.query(models.Product).filter(
                models.Product.id == item_data.product_id
            ).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {item_data.product_id} not found"
                )

        # 3. Create the Purchase Order
        new_po = models.PurchaseOrder(
            reference_no = generate_reference_number(db),
            vendor_id    = po_data.vendor_id,
            notes        = po_data.notes,
            subtotal     = 0,
            tax_amount   = 0,
            total_amount = 0,
            status       = models.POStatus.DRAFT
        )
        db.add(new_po)
        db.flush()

        # 4. Create each line item
        created_items = []
        for item_data in po_data.items:
            line_total = round(item_data.quantity * item_data.unit_price, 2)
            po_item = models.POItem(
                purchase_order_id = new_po.id,
                product_id        = item_data.product_id,
                quantity          = item_data.quantity,
                unit_price        = item_data.unit_price,
                line_total        = line_total
            )
            db.add(po_item)
            created_items.append(po_item)

        db.flush()

        # 5. Calculate totals with 5% tax
        totals = calculate_totals(created_items)
        new_po.subtotal     = totals["subtotal"]
        new_po.tax_amount   = totals["tax_amount"]
        new_po.total_amount = totals["total_amount"]

        # 6. Commit everything
        db.commit()
        db.refresh(new_po)
        return new_po

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating purchase order: {str(e)}"
        )


# ─────────────────────────────────────────────
# PATCH /api/purchase-orders/{id}/status
# ─────────────────────────────────────────────
@router.patch("/{po_id}/status", response_model=schemas.PurchaseOrderResponse)
def update_po_status(
    po_id: int,
    update_data: schemas.PurchaseOrderUpdate,
    db: Session = Depends(get_db)
):
    try:
        po = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.id == po_id
        ).first()

        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order {po_id} not found"
            )

        old_status = str(po.status.value) if po.status else "Unknown"

        if update_data.status:
            po.status = update_data.status
        if update_data.notes is not None:
            po.notes = update_data.notes

        new_status_val = str(update_data.status.value) if update_data.status else old_status

        # Notify Node.js server
        try:
            httpx.post("http://localhost:3001/notify", json={
                "reference_no": po.reference_no,
                "old_status"  : old_status,
                "new_status"  : new_status_val
            }, timeout=2)
        except Exception:
            pass

        db.commit()
        db.refresh(po)
        return po

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating PO status: {str(e)}"
        )


# ─────────────────────────────────────────────
# DELETE /api/purchase-orders/{id}
# ─────────────────────────────────────────────
@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(po_id: int, db: Session = Depends(get_db)):
    try:
        po = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.id == po_id
        ).first()

        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order {po_id} not found"
            )

        db.delete(po)
        db.commit()
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting purchase order: {str(e)}"
        )