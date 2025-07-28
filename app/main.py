from fastapi import FastAPI
from app.products.router import router as products_router
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Metal products",
    description="Website for selling metal products",
    # lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(products_router)
