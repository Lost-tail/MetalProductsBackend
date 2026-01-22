from datetime import datetime
import os
from typing import Annotated, List, Literal, Optional
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import asc, desc, select
from app.auth.dependencies import get_admin_user, get_current_user
from app.auth.utils import download_file, remove_file
from app.db import get_session
from app.settings import settings
from app.users.models import User
from .models import Product
from . import schemas

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
async def create_product(
    product: schemas.ProductCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = Product(**product.model_dump())
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db


@router.get("/{id}", response_model=Product)
async def read_product(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[Optional[User], Depends(get_current_user)],
):
    product = await session.get(Product, id)

    # Check if id exists. If not, return 404 not found response
    if not product or (
        not product.is_active and (not client or client.role != "admin")
    ):
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")

    if product.images:
        product.images = [f"{settings.SERVER_HOST}{image}" for image in product.images]
    return product


@router.patch("/{id}", response_model=Product, dependencies=[Depends(get_admin_user)])
async def update_product(
    id: uuid.UUID,
    product_update: schemas.ProductUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = await session.get(Product, id)
    if not product_db:
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")

    update_data = product_update.model_dump(exclude_unset=True)
    if update_data.get("images"):
        for image in product_db.images:
            if image not in update_data["images"]:
                await remove_file(image)
    for field, value in update_data.items():
        setattr(product_db, field, value)
    product_db.updated_at = datetime.now()
    session.add(product_db)
    await session.commit()
    await session.refresh(product_db)
    return product_db


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
async def delete_product(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    product_db = await session.get(Product, id)

    if product_db:
        await session.delete(product_db)
        await session.commit()
    else:
        raise HTTPException(status_code=404, detail=f"Product with id {id} not found")

    return None


@router.get("/", response_model=List[Product])
async def read_list_product(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[Optional[User], Depends(get_current_user)],
    category_id: Optional[uuid.UUID] = Query(None),
    is_main: Optional[bool] = Query(None),
    offset: int = 0,
    limit: Annotated[int, Query()] = 100,
    sort_by: Optional[Literal["id", "name", "rub_price", "created_at"]] = "id",
    order: Optional[Literal["asc", "desc"]] = "desc",
):
    query = select(Product)
    if not client or client.role != "admin":
        query = query.where(Product.is_active)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if is_main is not None:
        query = query.where(Product.is_main == is_main)
    query = query.offset(offset).limit(limit)
    if order == "asc":
        query = query.order_by(asc(sort_by))
    else:
        query = query.order_by(desc(sort_by))
    results = await session.exec(query)
    results.all()
    for product in results:
        if product.images:
            product.images = [
                f"{settings.SERVER_HOST}{image}" for image in product.images
            ]
    return results


@router.post("/add-image/{id}", dependencies=[Depends(get_admin_user)])
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
        # Генерируем путь для сохранения
        file_location = await download_file(file, UPLOAD_DIR)
        product.images = list(set(product.images + [f"api/{file_location}"]))
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    except Exception as e:
        return HTTPException(
            status_code=500, detail={"message": f"Произошла ошибка: {str(e)}"}
        )
