from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from app.settings import settings
from app.products.router import router as products_router
from app.users.router import router as users_router
from app.orders.router import router as orders_router
from app.categories.router import router as categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url(
        settings.REDIS_URL.unicode_string(), encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_client)
    yield  # App runs here


app = FastAPI(
    title="Metal products",
    description="Website for selling metal products",
    lifespan=lifespan,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9000",
        "http://127.0.0.1:9000",
        "http://localhost:9001",
        "http://127.0.0.1:9001",
        "http://localhost:5173",
    ],  # Specific allowed origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
app.mount("/api/static", StaticFiles(directory="static"), name="static")
app.include_router(products_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
