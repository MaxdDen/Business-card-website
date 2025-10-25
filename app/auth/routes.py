import os
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.rate_limit import login_limiter
from app.auth.security import create_access_token, verify_password, hash_password
from app.auth.security_headers import set_secure_cookie, delete_secure_cookie
from app.database.db import query_one, execute
from email_validator import validate_email, EmailNotValidError
from app.site.middleware import get_language_from_request, get_supported_languages_from_request, get_language_urls_from_request, get_cms_url, get_cms_dashboard_url


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def add_template_functions(context: dict) -> dict:
    """Добавить глобальные функции в контекст шаблона"""
    context.update({
        "get_cms_url": get_cms_url,
        "get_cms_dashboard_url": get_cms_dashboard_url
    })
    return context


def _get_user_by_email(email: str) -> Optional[dict]:
    return query_one("SELECT id, email, password_hash, role FROM users WHERE email = ?", (email,))


def get_text(page: str, key: str, lang: str = "en") -> str:
    """Получить текст из БД"""
    try:
        result = query_one(
            "SELECT value FROM texts WHERE page = ? AND key = ? AND lang = ?",
            (page, key, lang)
        )
        return result.get("value", "") if result else ""
    except Exception:
        return ""


def get_language_from_url(request: Request) -> str:
    """Получить язык из URL запроса"""
    from app.site.config import get_default_language
    
    url_path = str(request.url.path)
    
    # НОВАЯ СТРУКТУРА: домен → язык → страница
    # Универсальная проверка для всех типов страниц: /{lang}/...
    if url_path.startswith('/ua/'):
        return 'ua'
    elif url_path.startswith('/ru/'):
        return 'ru'
    elif url_path.startswith('/en/'):
        return 'en'
    elif url_path == '/ua':
        return 'ua'
    elif url_path == '/ru':
        return 'ru'
    elif url_path == '/en':
        return 'en'
    else:
        return get_default_language()

def get_cms_redirect_url(lang: str) -> str:
    """Получить URL для редиректа на CMS с учетом языка"""
    from app.site.config import get_default_language
    
    default_lang = get_default_language()
    
    # Для языка по умолчанию не добавляем префикс
    if lang == default_lang:
        return "/cms/"
    else:
        return f"/{lang}/cms/"


def get_login_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для страницы логина"""
    translations = {}
    
    # Список ключей переводов для логина
    translation_keys = [
        'title', 'subtitle', 'email', 'password', 'password_placeholder',
        'forgot_password', 'login_button', 'no_account', 'register_link', 
        'invalid_email', 'password_too_short', 'invalid_credentials', 'login_success'
    ]
    
    for key in translation_keys:
        translations[key] = get_text('login', key, lang)
    
    return translations


def get_header_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для Header"""
    translations = {}
    
    # Список ключей переводов для Header
    translation_keys = ['theme', 'home']
    
    for key in translation_keys:
        translations[key] = get_text('header', key, lang)
    
    return translations




@router.get("/login")
async def login_form(request: Request):
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем URL для редиректа после логина
    next_url = request.query_params.get("next", get_cms_redirect_url(lang))
    
    # Получаем переводы для логина и header
    translations = get_login_translations(lang)
    header_translations = get_header_translations(lang)
    translations.update(header_translations)
    
    context = {
        "request": request,
        "lang": lang,
        "supported_languages": supported_languages,
        "language_urls": language_urls,
        "next_url": next_url,
        "t": translations
    }
    return templates.TemplateResponse("crm/login.html", add_template_functions(context))

# Языковые роуты для логина
@router.get("/ru/login")
async def login_form_ru(request: Request):
    return await login_form(request)

@router.get("/ua/login")
async def login_form_ua(request: Request):
    return await login_form(request)

@router.get("/en/login")
async def login_form_en(request: Request):
    return await login_form(request)

# POST роуты для языковых версий login
@router.post("/ru/login")
async def login_ru(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    return await login(request, response, email, password)

@router.post("/ua/login")
async def login_ua(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    return await login(request, response, email, password)

@router.post("/en/login")
async def login_en(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    return await login(request, response, email, password)


@router.post("/login")
async def login(request: Request, response: Response, email: str = Form(...), password: str = Form(...)):
    client_key = request.client.host if request.client else "unknown"
    if not login_limiter.allow(f"login:{client_key}"):
        raise HTTPException(status_code=429, detail="Too many attempts. Try later.")

    # Получаем язык и переводы для отображения ошибок
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    translations = get_login_translations(lang)
    header_translations = get_header_translations(lang)
    translations.update(header_translations)
    
    # Получаем URL для редиректа после логина
    next_url = request.query_params.get("next", get_cms_redirect_url(lang))

    # validate email
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        context = {
            "request": request, 
            "error": translations.get('invalid_email', 'Invalid email format'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "next_url": next_url,
            "t": translations
        }
        return templates.TemplateResponse("crm/login.html", add_template_functions(context), status_code=400)

    # validate password length
    if len(password) < 8:
        context = {
            "request": request, 
            "error": translations.get('password_too_short', 'Password must be at least 8 characters'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "next_url": next_url,
            "t": translations
        }
        return templates.TemplateResponse("crm/login.html", add_template_functions(context), status_code=400)
    if len(password.encode('utf-8')) > 72:
        context = {
            "request": request, 
            "error": "Password too long (maximum 72 bytes)",
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "next_url": next_url,
            "t": translations
        }
        return templates.TemplateResponse("crm/login.html", add_template_functions(context), status_code=400)

    user = _get_user_by_email(email)
    if not user:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"User not found for email: {email}")
        context = {
            "request": request, 
            "error": translations.get('invalid_credentials', 'Invalid email or password'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "next_url": next_url,
            "t": translations
        }
        return templates.TemplateResponse("crm/login.html", add_template_functions(context), status_code=401)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting login for user: {email}")
    logger.info(f"Stored hash: {user['password_hash'][:20]}...")
    
    if not verify_password(password, user["password_hash"]):
        logger.warning(f"Password verification failed for user: {email}")
        context = {
            "request": request, 
            "error": translations.get('invalid_credentials', 'Invalid email or password'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "next_url": next_url,
            "t": translations
        }
        return templates.TemplateResponse("crm/login.html", add_template_functions(context), status_code=401)

    token = create_access_token(subject=str(user["id"]), role=user["role"])
    # Используем сохраненный URL для редиректа или дефолтный
    resp = RedirectResponse(url=next_url, status_code=302)
    # Устанавливаем безопасный HttpOnly cookie для JWT
    set_secure_cookie(
        response=resp,
        key="access_token",
        value=token,
        max_age=int(os.getenv("JWT_EXPIRES_MINUTES", "15")) * 60,
        httponly=True,
        samesite="lax"
    )
    return resp


def get_register_translations(lang: str) -> Dict[str, str]:
    """Получить переводы для страницы регистрации"""
    translations = {}
    
    # Список ключей переводов для регистрации
    translation_keys = [
        'title', 'subtitle', 'email', 'email_placeholder', 'password_label', 
        'password_placeholder', 'confirm_password', 'confirm_password_placeholder',
        'create_account', 'already_have_account', 'sign_in', 'invalid_email',
        'password_too_short', 'passwords_dont_match', 'email_exists', 'registration_success'
    ]
    
    for key in translation_keys:
        translations[key] = get_text('register', key, lang)
    
    return translations

@router.get("/register")
async def register_form(request: Request):
    # Получаем язык и настройки мультиязычности
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    
    # Получаем переводы для регистрации и header
    translations = get_register_translations(lang)
    header_translations = get_header_translations(lang)
    translations.update(header_translations)
    
    context = {
        "request": request,
        "lang": lang,
        "supported_languages": supported_languages,
        "language_urls": language_urls,
        "t": translations
    }
    return templates.TemplateResponse("crm/register.html", add_template_functions(context))

# Языковые роуты для регистрации
@router.get("/ru/register")
async def register_form_ru(request: Request):
    return await register_form(request)

@router.get("/ua/register")
async def register_form_ua(request: Request):
    return await register_form(request)

@router.get("/en/register")
async def register_form_en(request: Request):
    return await register_form(request)

# POST роуты для языковых версий register
@router.post("/ru/register")
async def register_ru(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    return await register(request, email, password, confirm_password)

@router.post("/ua/register")
async def register_ua(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    return await register(request, email, password, confirm_password)

@router.post("/en/register")
async def register_en(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    return await register(request, email, password, confirm_password)


@router.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    # Получаем язык и переводы для отображения ошибок
    lang = get_language_from_request(request)
    supported_languages = get_supported_languages_from_request(request)
    language_urls = get_language_urls_from_request(request)
    translations = get_register_translations(lang)
    header_translations = get_header_translations(lang)
    translations.update(header_translations)
    
    # validate email
    try:
        email = validate_email(email, check_deliverability=False).normalized
    except EmailNotValidError:
        context = {
            "request": request, 
            "error": translations.get('invalid_email', 'Invalid email format'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=400)

    # validate password
    if len(password) < 8:
        context = {
            "request": request, 
            "error": translations.get('password_too_short', 'Password must be at least 8 characters'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=400)
    if len(password.encode('utf-8')) > 72:
        context = {
            "request": request, 
            "error": "Password too long (maximum 72 bytes)",
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=400)
    if password != confirm_password:
        context = {
            "request": request, 
            "error": translations.get('passwords_dont_match', 'Passwords do not match'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=400)

    # check unique
    existing = _get_user_by_email(email)
    if existing:
        context = {
            "request": request, 
            "error": translations.get('email_exists', 'User with this email already exists'),
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=400)

    # store bcrypt hash
    try:
        password_hash = hash_password(password)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Password hashing failed: {e}")
        context = {
            "request": request, 
            "error": "Password creation error. Try another password.",
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=500)
    
    try:
        user_id = execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, "editor"),
        )
    except Exception as e:
        context = {
            "request": request, 
            "error": f"User creation error: {str(e)}",
            "lang": lang,
            "supported_languages": supported_languages,
            "language_urls": language_urls,
            "t": translations
        }
        return templates.TemplateResponse("crm/register.html", add_template_functions(context), status_code=500)

    # auto login
    token = create_access_token(subject=str(user_id), role="editor")
    # Получаем язык из URL для редиректа
    lang = get_language_from_url(request)
    redirect_url = get_cms_redirect_url(lang)
    resp = RedirectResponse(url=redirect_url, status_code=302)
    # Устанавливаем безопасный HttpOnly cookie для JWT
    set_secure_cookie(
        response=resp,
        key="access_token",
        value=token,
        max_age=int(os.getenv("JWT_EXPIRES_MINUTES", "15")) * 60,
        httponly=True,
        samesite="lax"
    )
    return resp

@router.get("/logout")
@router.post("/logout")
async def logout() -> Response:
    resp = RedirectResponse(url="/login", status_code=302)
    # Удаляем безопасный cookie
    delete_secure_cookie(resp, "access_token")
    return resp

# Языковые роуты для logout
@router.get("/ru/logout")
@router.post("/ru/logout")
async def logout_ru() -> Response:
    resp = RedirectResponse(url="/ru/login", status_code=302)
    # Удаляем безопасный cookie
    delete_secure_cookie(resp, "access_token")
    return resp

@router.get("/ua/logout")
@router.post("/ua/logout")
async def logout_ua() -> Response:
    resp = RedirectResponse(url="/ua/login", status_code=302)
    # Удаляем безопасный cookie
    delete_secure_cookie(resp, "access_token")
    return resp

@router.get("/en/logout")
@router.post("/en/logout")
async def logout_en() -> Response:
    resp = RedirectResponse(url="/en/login", status_code=302)
    # Удаляем безопасный cookie
    delete_secure_cookie(resp, "access_token")
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


