# google_auth.py - Handles Google OAuth login

import os
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from app import models, schemas
from app.database import SessionLocal
from app.auth import create_access_token, hash_password
import secrets

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:5500")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"
REDIRECT_URI     = "http://localhost:8000/api/auth/google/callback"


# ─────────────────────────────────────────────
# GET /api/auth/google
# Redirects user to Google login page
# ─────────────────────────────────────────────
@router.get("/google")
def google_login():
    params = {
        "client_id"    : GOOGLE_CLIENT_ID,
        "redirect_uri" : REDIRECT_URI,
        "response_type": "code",
        "scope"        : "openid email profile",
        "access_type"  : "offline",
        "prompt"       : "select_account"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query}")


# ─────────────────────────────────────────────
# GET /api/auth/google/callback
# Google redirects here after user logs in
# ─────────────────────────────────────────────
@router.get("/google/callback")
async def google_callback(code: str):
    try:
        # 1. Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_res = await client.post(GOOGLE_TOKEN_URL, data={
                "code"         : code,
                "client_id"    : GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri" : REDIRECT_URI,
                "grant_type"   : "authorization_code"
            })
            token_data = token_res.json()

            if "error" in token_data:
                raise HTTPException(status_code=400, detail=token_data["error"])

            access_token = token_data["access_token"]

            # 2. Get user info from Google
            user_res = await client.get(
                GOOGLE_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            google_user = user_res.json()

        # 3. Find or create user in our database
        db = SessionLocal()
        try:
            email    = google_user.get("email")
            name     = google_user.get("name", email.split("@")[0])
            username = email.split("@")[0]

            # Check if user already exists
            user = db.query(models.User).filter(
                models.User.email == email
            ).first()

            if not user:
                # Create new user from Google account
                # Generate random password since they login via Google
                random_password = secrets.token_hex(16)
                user = models.User(
                    username        = username,
                    email           = email,
                    hashed_password = hash_password(random_password)
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        finally:
            db.close()

        # 4. Create our JWT token for this user
        jwt_token = create_access_token(data={"sub": user.username})

        # 5. Redirect to frontend with token in URL
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login.html?token={jwt_token}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth failed: {str(e)}"
        )