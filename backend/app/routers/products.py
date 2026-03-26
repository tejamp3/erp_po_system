# products.py - All API routes related to Products

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os
import google.generativeai as genai
from dotenv import load_dotenv

from app.database import get_db
from app import models, schemas

load_dotenv()
router = APIRouter()


# ─────────────────────────────────────────────
# GET /api/products
# Returns all products
# ─────────────────────────────────────────────
@router.get("/", response_model=List[schemas.ProductResponse])
def get_all_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        products = db.query(models.Product).offset(skip).limit(limit).all()
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching products: {str(e)}"
        )


# ─────────────────────────────────────────────
# GET /api/products/{id}
# Returns a single product by ID
# ─────────────────────────────────────────────
@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching product: {str(e)}"
        )


# ─────────────────────────────────────────────
# POST /api/products
# Creates a new product
# ─────────────────────────────────────────────
@router.post("/", response_model=schemas.ProductResponse,
             status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    try:
        # Check for duplicate SKU
        existing = db.query(models.Product).filter(
            models.Product.sku == product_data.sku
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )

        new_product = models.Product(**product_data.model_dump())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )


# ─────────────────────────────────────────────
# PUT /api/products/{id}
# Updates an existing product
# ─────────────────────────────────────────────
@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: schemas.ProductUpdate,
    db: Session = Depends(get_db)
):
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)
        return product

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating product: {str(e)}"
        )


# ─────────────────────────────────────────────
# DELETE /api/products/{id}
# Deletes a product
# ─────────────────────────────────────────────
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )

        db.delete(product)
        db.commit()
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting product: {str(e)}"
        )


# ─────────────────────────────────────────────
# POST /api/products/ai-description
# 🤖 BONUS: Gemini AI auto-generates product description
# ─────────────────────────────────────────────
@router.post("/ai-description", response_model=schemas.AIDescriptionResponse)
def generate_ai_description(request: schemas.AIDescriptionRequest):
    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your-gemini-api-key-here":
            # Fallback if no API key is set yet
            return {
                "description": f"The {request.product_name} is a premium-quality "
                               f"{request.category} product designed for modern businesses. "
                               f"Built to deliver exceptional performance and long-lasting reliability."
            }

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")

        prompt = (
            f"Write a professional 2-sentence marketing description for a product "
            f"called '{request.product_name}' in the '{request.category}' category. "
            f"Be concise, engaging, and business-focused."
        )

        response = model.generate_content(prompt)
        return {"description": response.text.strip()}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI description generation failed: {str(e)}"
        )