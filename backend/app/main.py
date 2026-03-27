# main.py - Entry point of our FastAPI application
from app.routers import vendors, products, purchase_orders, auth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import vendors, products, purchase_orders, auth, google_auth

# ─────────────────────────────────────────────
# Create all tables in PostgreSQL automatically
# This runs when the server starts
# ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# Initialize FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title="ERP Purchase Order Management System",
    description="A system to manage vendors, products, and purchase orders",
    version="1.0.0"
)

# ─────────────────────────────────────────────
# CORS Middleware
# Allows our frontend (HTML files) to talk to
# this backend API without being blocked
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, replace * with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Register Routers
# Each router handles a group of related APIs
# ─────────────────────────────────────────────
app.include_router(vendors.router,          prefix="/api/vendors",        tags=["Vendors"])
app.include_router(products.router,         prefix="/api/products",       tags=["Products"])
app.include_router(purchase_orders.router,  prefix="/api/purchase-orders",tags=["Purchase Orders"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(google_auth.router, prefix="/api/auth", tags=["Google OAuth"])
# ─────────────────────────────────────────────
# Root endpoint - just to test if server is up
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "ERP PO Management System is running!",
        "docs": "Visit /docs for API documentation"
    }