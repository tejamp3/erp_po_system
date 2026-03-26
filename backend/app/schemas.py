# schemas.py - Defines data shapes for API requests and responses
# Pydantic validates all incoming and outgoing data automatically

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────
# ENUM - Must match the one in models.py
# ─────────────────────────────────────────────
class POStatus(str, Enum):
    DRAFT     = "Draft"
    CONFIRMED = "Confirmed"
    RECEIVED  = "Received"
    CANCELLED = "Cancelled"


# ═══════════════════════════════════════════════
# VENDOR SCHEMAS
# ═══════════════════════════════════════════════

# Base = shared fields between Create and Response
class VendorBase(BaseModel):
    name    : str
    contact : str
    email   : Optional[str] = None
    phone   : Optional[str] = None
    rating  : Optional[float] = 0.0

    # Validator: rating must be between 0 and 5
    @field_validator("rating")
    @classmethod
    def rating_must_be_valid(cls, v):
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("Rating must be between 0.0 and 5.0")
        return v

# Used when CREATING a vendor (user sends this)
class VendorCreate(VendorBase):
    pass  # Inherits everything from VendorBase

# Used when UPDATING a vendor (all fields optional)
class VendorUpdate(BaseModel):
    name    : Optional[str]   = None
    contact : Optional[str]   = None
    email   : Optional[str]   = None
    phone   : Optional[str]   = None
    rating  : Optional[float] = None

# Used when RETURNING vendor data (includes DB fields)
class VendorResponse(VendorBase):
    id         : int
    created_at : Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows reading from SQLAlchemy model


# ═══════════════════════════════════════════════
# PRODUCT SCHEMAS
# ═══════════════════════════════════════════════

class ProductBase(BaseModel):
    name        : str
    sku         : str
    category    : Optional[str]   = None
    unit_price  : float
    stock_level : Optional[int]   = 0
    description : Optional[str]   = None

    # Validator: price must be positive
    @field_validator("unit_price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Unit price must be greater than 0")
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name        : Optional[str]   = None
    sku         : Optional[str]   = None
    category    : Optional[str]   = None
    unit_price  : Optional[float] = None
    stock_level : Optional[int]   = None
    description : Optional[str]   = None

class ProductResponse(ProductBase):
    id         : int
    created_at : Optional[datetime] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# PO ITEM SCHEMAS (Line items inside a PO)
# ═══════════════════════════════════════════════

class POItemBase(BaseModel):
    product_id : int
    quantity   : int
    unit_price : float

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v

class POItemCreate(POItemBase):
    pass

class POItemResponse(POItemBase):
    id         : int
    line_total : float
    product    : Optional[ProductResponse] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# PURCHASE ORDER SCHEMAS
# ═══════════════════════════════════════════════

class PurchaseOrderBase(BaseModel):
    vendor_id : int
    notes     : Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    # When creating a PO, user sends a list of items
    items : List[POItemCreate]

class PurchaseOrderUpdate(BaseModel):
    status : Optional[POStatus] = None
    notes  : Optional[str]      = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id           : int
    reference_no : str
    subtotal     : float
    tax_amount   : float
    total_amount : float
    status       : POStatus
    created_at   : Optional[datetime] = None
    vendor       : Optional[VendorResponse]   = None
    items        : Optional[List[POItemResponse]] = []

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# AI DESCRIPTION SCHEMA
# ═══════════════════════════════════════════════

class AIDescriptionRequest(BaseModel):
    product_name : str
    category     : Optional[str] = "General"

class AIDescriptionResponse(BaseModel):
    description : str

    # ═══════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════

class UserCreate(BaseModel):
    username : str
    email    : str
    password : str

class UserResponse(BaseModel):
    id       : int
    username : str
    email    : str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token : str
    token_type   : str

class LoginRequest(BaseModel):
    username : str
    password : str