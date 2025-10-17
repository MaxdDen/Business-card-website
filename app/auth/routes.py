import os
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app.auth.rate_limit import login_limiter
from app.auth.security import create_access_token, verify_password
from app.database.db import query_one


router = APIRouter()


def _get_user_by_email(email: str) -> Optional[dict]:
    return query_one("SELECT id, email, password_hash, role FROM users WHERE email = ?", (email,))


@router.get("/login")
async def login_form() -> dict:
    return {"status": "ok", "message": "Submit POST /login with email & password"}


@router.post("/login")
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    client_key = request.client.host if request.client else "unknown"
    if not login_limiter.allow(f"login:{client_key}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")

    user = _get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=str(user["id"]), role=user["role"])
    resp = RedirectResponse(url="/cms", status_code=302)
    # HttpOnly cookie for JWT
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        max_age=int(os.getenv("JWT_EXPIRES_MINUTES", "15")) * 60,
        path="/",
    )
    return resp


@router.post("/logout")
async def logout() -> Response:
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("access_token", path="/")
    return resp


def require_auth(request: Request) -> dict:
    from app.auth.security import decode_token  # lazy import to avoid cycles

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401)
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    return payload


@router.get("/cms")
async def cms_home(user=Depends(require_auth)):
    return {"message": "Welcome to CMS", "user": {"id": user.get("sub"), "role": user.get("role")}}


