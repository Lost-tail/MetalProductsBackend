from datetime import datetime
from typing import Annotated, Literal, Optional
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import asc, desc, select
from app.auth.dependencies import get_admin_user, get_current_user
from app.db import get_session
from app.users.models import User
from .models import Category
from . import schemas

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post(
    "/",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)],
)
async def create_category(
    category: schemas.CategoryCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    category_db = Category(**category.model_dump())
    session.add(category_db)
    await session.commit()
    await session.refresh(category_db)
    return category_db


@router.get("/{id}", response_model=Category)
async def read_category(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[Optional[User], Depends(get_current_user)],
):
    category = await session.get(Category, id)
    print(client)

    # Check if id exists. If not, return 404 not found response
    if not category or (
        not category.is_active and (not client or client.role != "admin")
    ):
        raise HTTPException(status_code=404, detail=f"Category with id {id} not found")

    return category


@router.patch("/{id}", response_model=Category, dependencies=[Depends(get_admin_user)])
async def update_category(
    id: uuid.UUID,
    category_update: schemas.CategoryUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    category_db = await session.get(Category, id)
    if not category_db:
        raise HTTPException(status_code=404, detail=f"Category with id {id} not found")

    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category_db, field, value)
    category_db.updated_at = datetime.now()
    session.add(category_db)
    await session.commit()
    await session.refresh(category_db)
    return category_db


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
async def delete_category(
    id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    category_db = await session.get(Category, id)

    if category_db:
        await session.delete(category_db)
        await session.commit()
    else:
        raise HTTPException(status_code=404, detail=f"Category with id {id} not found")

    return None


@router.get(
    "/",
)
async def read_list_category(
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[Optional[User], Depends(get_current_user)],
    offset: int = 0,
    limit: Annotated[int, Query()] = 100,
    sort_by: Optional[Literal["id", "name", "created_at"]] = "id",
    order: Optional[Literal["asc", "desc"]] = "desc",
):
    query = select(Category)
    if not client or client.role != "admin":
        query = query.where(Category.is_active)
    query = query.offset(offset).limit(limit)
    if order == "asc":
        query = query.order_by(asc(sort_by))
    else:
        query = query.order_by(desc(sort_by))
    results = await session.exec(query)

    return results.all()
