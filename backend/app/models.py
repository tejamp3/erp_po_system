# models.py - Defines all database tables as Python classes
# SQLAlchemy will automatically create these tables in PostgreSQL

from sqlalchemy import (
    Column, Integer, String, Float, 
    ForeignKey, DateTime, Enum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

# Import Base from our database.py file
from app.database import Base


# ─────────────────────────────────────────────
# ENUM for Purchase Order Status
# Like a dropdown with fixed allowed values
# ─────────────────────────────────────────────
class POStatus(str, enum.Enum):
    DRAFT     = "Draft"
    CONFIRMED = "Confirmed"
    RECEIVED  = "Received"
    CANCELLED = "Cancelled"


# ─────────────────────────────────────────────
# TABLE 1: VENDORS
# Stores supplier/vendor information
# ─────────────────────────────────────────────
class Vendor(Base):
    __tablename__ = "vendors"  # Actual table name in PostgreSQL

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False, unique=True)
    contact    = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=True)
    phone      = Column(String(20),  nullable=True)
    rating     = Column(Float, default=0.0)  # Rating out of 5
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: One vendor can have MANY purchase orders
    # This lets us do vendor.purchase_orders to get all POs
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")


# ─────────────────────────────────────────────
# TABLE 2: PRODUCTS
# Stores product/item catalog information
# ─────────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(150), nullable=False)
    sku         = Column(String(50),  nullable=False, unique=True)  # Stock Keeping Unit
    category    = Column(String(100), nullable=True)
    unit_price  = Column(Float,       nullable=False)
    stock_level = Column(Integer,     default=0)
    description = Column(Text,        nullable=True)  # AI will fill this later!
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: One product can appear in MANY PO items
    po_items = relationship("POItem", back_populates="product")


# ─────────────────────────────────────────────
# TABLE 3: PURCHASE ORDERS
# The main order document
# ─────────────────────────────────────────────
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id           = Column(Integer, primary_key=True, index=True)
    reference_no = Column(String(50), nullable=False, unique=True)  # e.g. PO-2024-001
    vendor_id    = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    subtotal     = Column(Float, default=0.0)   # Before tax
    tax_amount   = Column(Float, default=0.0)   # 5% tax
    total_amount = Column(Float, default=0.0)   # Final amount (subtotal + tax)
    status       = Column(Enum(POStatus), default=POStatus.DRAFT)
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # This links back to the Vendor table
    vendor = relationship("Vendor", back_populates="purchase_orders")
    
    # One PO can have MANY line items (products)
    items  = relationship("POItem", back_populates="purchase_order", 
                         cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# TABLE 4: PO ITEMS (Line Items)
# Each row = one product inside a purchase order
# Example: PO-001 has 3 items: 2x Chair, 5x Desk, 1x Lamp
# ─────────────────────────────────────────────
class POItem(Base):
    __tablename__ = "po_items"

    id                = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id        = Column(Integer, ForeignKey("products.id"),        nullable=False)
    quantity          = Column(Integer, nullable=False, default=1)
    unit_price        = Column(Float,   nullable=False)  # Price at time of order
    line_total        = Column(Float,   nullable=False)  # quantity × unit_price

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product        = relationship("Product",       back_populates="po_items")
    # ─────────────────────────────────────────────
# TABLE 5: USERS
# Stores login credentials
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, nullable=False)
    email           = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(Integer, default=1)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())