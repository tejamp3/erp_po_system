# vendors.py - All API routes related to Vendors
# Handles Create, Read, Update, Delete (CRUD) operations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

# APIRouter groups all vendor-related routes together
router = APIRouter()


# ─────────────────────────────────────────────
# GET /api/vendors
# Returns a list of all vendors
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.VendorResponse])
def get_all_vendors(
    skip: int = 0,      # Pagination: how many to skip
    limit: int = 100,   # Pagination: max how many to return
    db: Session = Depends(get_db)
):
    try:
        vendors = db.query(models.Vendor).offset(skip).limit(limit).all()
        return vendors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching vendors: {str(e)}"
        )


# ─────────────────────────────────────────────
# GET /api/vendors/{id}
# Returns a single vendor by ID
# ─────────────────────────────────────────────
@router.get("/{vendor_id}", response_model=schemas.VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    try:
        vendor = db.query(models.Vendor).filter(
            models.Vendor.id == vendor_id
        ).first()

        # If no vendor found, return 404 error
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id {vendor_id} not found"
            )
        return vendor
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching vendor: {str(e)}"
        )


# ─────────────────────────────────────────────
# POST /api/vendors
# Creates a new vendor
# ─────────────────────────────────────────────
@router.post("/", response_model=schemas.VendorResponse, 
             status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_data: schemas.VendorCreate,  # Validated input from user
    db: Session = Depends(get_db)
):
    try:
        # Check if vendor with same name already exists
        existing = db.query(models.Vendor).filter(
            models.Vendor.name == vendor_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor with name '{vendor_data.name}' already exists"
            )

        # Create new Vendor object
        new_vendor = models.Vendor(**vendor_data.model_dump())

        db.add(new_vendor)      # Stage the new record
        db.commit()             # Save to database
        db.refresh(new_vendor)  # Get the saved data back (including id)

        return new_vendor

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()  # Undo any changes if error occurs
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating vendor: {str(e)}"
        )


# ─────────────────────────────────────────────
# PUT /api/vendors/{id}
# Updates an existing vendor
# ─────────────────────────────────────────────
@router.put("/{vendor_id}", response_model=schemas.VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_data: schemas.VendorUpdate,
    db: Session = Depends(get_db)
):
    try:
        vendor = db.query(models.Vendor).filter(
            models.Vendor.id == vendor_id
        ).first()

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id {vendor_id} not found"
            )

        # Only update fields that were actually sent
        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        db.commit()
        db.refresh(vendor)
        return vendor

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vendor: {str(e)}"
        )


# ─────────────────────────────────────────────
# DELETE /api/vendors/{id}
# Deletes a vendor
# ─────────────────────────────────────────────
@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    try:
        vendor = db.query(models.Vendor).filter(
            models.Vendor.id == vendor_id
        ).first()

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor with id {vendor_id} not found"
            )

        db.delete(vendor)
        db.commit()
        return None  # 204 returns no content

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting vendor: {str(e)}"
        )