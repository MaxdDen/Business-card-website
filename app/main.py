import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.auth.csrf import CSRFMiddleware
from app.auth.routes import router as auth_router
from dotenv import load_dotenv
from app.database.db import ensure_database_initialized, smoke_test

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    ensure_database_initialized()
    ok = smoke_test()
    logging.info("DB smoke test: %s", "OK" if ok else "FAILED")
    yield

app = FastAPI(title="Business Card CMS", lifespan=lifespan)
app.add_middleware(CSRFMiddleware)
app.include_router(auth_router)

@app.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}
