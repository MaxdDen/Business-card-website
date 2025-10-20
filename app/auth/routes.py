import os
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.rate_limit import login_limiter
from app.auth.security import create_access_token, verify_password, hash_password
from app.database.db import query_one, execute
from email_validator import validate_email, EmailNotValidError


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_user_by_email(email: str) -> Optional[dict]:
    return query_one("SELECT id, email, password_hash, role FROM users WHERE email = ?", (email,))


@router.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    client_key = request.client.host if request.client else "unknown"
    if not login_limiter.allow(f"login:{client_key}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")

    # validate email
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Некорректный email"},
            status_code=400,
        )

    # validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Минимальная длина пароля — 8 символов"},
            status_code=400,
        )
    if len(password.encode('utf-8')) > 72:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Пароль слишком длинный (максимум 72 байта)"},
            status_code=400,
        )

    user = _get_user_by_email(email)
    if not user:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"User not found for email: {email}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверные учетные данные"},
            status_code=401,
        )
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting login for user: {email}")
    logger.info(f"Stored hash: {user['password_hash'][:20]}...")
    
    if not verify_password(password, user["password_hash"]):
        logger.warning(f"Password verification failed for user: {email}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверные учетные данные"},
            status_code=401,
        )

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


@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    # validate email
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Некорректный email"},
            status_code=400,
        )

    # validate password
    if len(password) < 8:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Минимальная длина пароля — 8 символов"},
            status_code=400,
        )
    if len(password.encode('utf-8')) > 72:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароль слишком длинный (максимум 72 байта)"},
            status_code=400,
        )
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароли не совпадают"},
            status_code=400,
        )

    # check unique
    existing = _get_user_by_email(email)
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь с таким email уже существует"},
            status_code=400,
        )

    # store bcrypt hash
    try:
        password_hash = hash_password(password)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Password hashing failed: {e}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Ошибка при создании пароля. Попробуйте другой пароль."},
            status_code=500,
        )
    
    try:
        user_id = execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, "editor"),
        )
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Ошибка при создании пользователя: {str(e)}"},
            status_code=500,
        )

    # auto login
    token = create_access_token(subject=str(user_id), role="editor")
    resp = RedirectResponse(url="/cms", status_code=302)
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

@router.get("/logout")
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


