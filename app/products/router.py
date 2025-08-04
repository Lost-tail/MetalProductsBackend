import os
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db import get_session
from app.settings import settings
from .models import Product
from . import schemas

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create(
    product: schemas.ProductCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = Product(product)
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db


@router.get("/{id}", response_model=Product)
async def read(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product = await session.get(Product, id)

    # Check if id exists. If not, return 404 not found response
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")

    return product


@router.put("/{id}", response_model=Product)
async def update(
    id: uuid.UUID,
    product_update: schemas.ProductUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = await session.get(Product, id)
    if not product_db:
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")

    hero_data = product_update.model_dump(exclude_unset=True)
    product_db.sqlmodel_update(hero_data)
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = await session.get(Product, id)

    if product_db:
        await session.delete(product_db)
        await session.commit()
    else:
        raise HTTPException(status_code=404, detail=f"Task with id {id} not found")

    return None


@router.get("/", response_model=List[Product])
async def read_list(
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    results = await session.exec(select(Product).offset(offset).limit(limit))

    return results.all()


@router.post("/add-image/{id}")
async def add_image(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile,
):
    try:
        # Проверяем, что файл является изображением
        if not file.content_type.startswith("image/"):
            return HTTPException(
                status_code=400, detail={"message": "Файл не является изображением"}
            )
        product = await session.get(Product, id)

        # Check if id exists. If not, return 404 not found response
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product with id {id} not found"
            )

        UPLOAD_DIR = "static/products"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Генерируем путь для сохранения
        file_location = os.path.join(UPLOAD_DIR, file.filename)

        # Сохраняем файл
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        product.sqlmodel_update(
            {"images": product.images + [f"{settings.SERVER_HOST}/{file_location}"]}
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    except Exception as e:
        return HTTPException(
            status_code=500, detail={"message": f"Произошла ошибка: {str(e)}"}
        )
