from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis

from app.settings import settings
from app.products.router import router as products_router
from app.users.router import router as users_router
from app.orders.router import router as orders_router


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
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(products_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(users_router, prefix="/api")
