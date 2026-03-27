# ERP Purchase Order Management System

A full-stack ERP system for managing Vendors, Products, and Purchase Orders with real-time notifications and AI-powered descriptions.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Frontend | HTML5, Bootstrap 5, Vanilla JS |
| Auth | JWT (python-jose, passlib) |
| Notifications | Node.js, Socket.IO |
| AI | Grok API |

---

## Project Structure
```
erp_po_system/
├── backend/
│   ├── app/
│   │   ├── main.py              # App entry point
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── models.py            # DB table definitions
│   │   ├── schemas.py           # Data validation
│   │   ├── auth.py              # JWT logic
│   │   └── routers/
│   │       ├── auth.py          # Login/Register APIs
│   │       ├── vendors.py       # Vendor CRUD APIs
│   │       ├── products.py      # Product CRUD + AI
│   │       └── purchase_orders.py # PO CRUD APIs
│   ├── .env                     # Secret config (not in Git)
│   └── requirements.txt
├── frontend/
│   ├── login.html               # Login/Register page
│   ├── index.html               # Dashboard
│   ├── create_po.html           # Create PO form
│   ├── css/style.css
│   └── js/
│       ├── app.js               # Dashboard logic
│       └── create_po.js         # PO form logic
├── notifications/
│   ├── server.js                # Socket.IO server
│   └── package.json
└── README.md
```

---

## Database Design

4 tables with proper relationships:
```
vendors (1) ──── (many) purchase_orders
purchase_orders (1) ──── (many) po_items
products (1) ──── (many) po_items
users — stores login credentials
```

**Design decisions:**
- `po_items` junction table allows multiple products per PO (normalization)
- Tax (5%) calculated server-side to prevent frontend tampering
- Reference numbers auto-generated as `PO-YYYY-XXXX`
- Cascade delete on PO items when PO is deleted

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/erp_po_system.git
cd erp_po_system
```

### 2. Setup PostgreSQL
- Create a database named `erp_po_db`
- Note your PostgreSQL username and password

### 3. Backend setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/erp_po_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your-gemini-api-key-here
```

Start the backend:
```bash
uvicorn app.main:app --reload
```
API runs at: `http://127.0.0.1:8000`
API docs at: `http://127.0.0.1:8000/docs`

### 4. Notifications setup
```bash
cd notifications
npm install
node server.js
```
Runs at: `http://localhost:3001`

### 5. Frontend
Open `frontend/login.html` directly in your browser.

---

## Key Features

- **Create PO** with multiple product rows — totals calculate live
- **5% tax** applied automatically server-side
- **JWT Authentication** — register/login with secure hashed passwords
- **Real-time notifications** — toast popup when PO status changes
- **AI Auto-Description** — Gemini generates product descriptions
- **Dashboard** with stat cards, search, status update, delete

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login, returns JWT |
| GET | /api/vendors/ | List all vendors |
| POST | /api/vendors/ | Create vendor |
| GET | /api/products/ | List all products |
| POST | /api/products/ | Create product |
| POST | /api/products/ai-description | AI generate description |
| GET | /api/purchase-orders/ | List all POs |
| POST | /api/purchase-orders/ | Create PO with items |
| PATCH | /api/purchase-orders/{id}/status | Update PO status |
| DELETE | /api/purchase-orders/{id} | Delete PO |
