import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.auth.csrf import CSRFMiddleware
from app.auth.middleware import AuthRedirectMiddleware
from app.auth.routes import router as auth_router
from app.cms.routes import router as cms_router
from dotenv import load_dotenv
from app.database.db import ensure_database_initialized, smoke_test, ensure_admin_user_exists

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    ensure_database_initialized()
    ok = smoke_test()
    logging.info("DB smoke test: %s", "OK" if ok else "FAILED")
    
    # Проверяем и создаем администратора
    ensure_admin_user_exists()
    
    yield

app = FastAPI(title="Business Card CMS", lifespan=lifespan)
app.add_middleware(CSRFMiddleware)
app.add_middleware(AuthRedirectMiddleware)
app.include_router(auth_router)
app.include_router(cms_router)

# Обработка 401 ошибок делегируется middleware

# Static and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
