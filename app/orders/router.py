from datetime import datetime
import os
from typing import Annotated, List, Optional
from typing_extensions import Literal
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import asc, desc, select
from app.db import get_session
from app.settings import settings
from .models import Product
from . import schemas
from app.auth.dependencies import get_admin_user, get_current_user
from .models import Order, OrderDetail, OrderProductLink
from .schemas import OrderCreate, OrderRead, OrderUpdate
from fastapi_limiter.depends import RateLimiter


router = APIRouter(prefix="/orders", tags=["orders"])


# CREATE Order (admin only)
@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def create_order(
    order_in: OrderCreate, session: Annotated[AsyncSession, Depends(get_session)]
):
    order = Order()
    session.add(order)
    await session.commit()
    await session.refresh(order)

    # Add OrderDetail
    detail = OrderDetail(**order_in.detail.model_dump(), order_id=order.id)
    session.add(detail)
    await session.commit()
    await session.refresh(detail)

    # Add OrderProductLinks
    for link in order_in.product_links:
        opl = OrderProductLink(
            order_id=order.id, product_id=link.product_id, quantity=link.quantity
        )
        session.add(opl)
    await session.commit()
    await session.refresh(order)
    await session.refresh(detail)
    return order


# READ Order (anyone)
@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_session)]
):
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# READ all Orders (anyone)
@router.get("/", response_model=List[OrderRead])
async def get_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = 0,
    limit: int = 100,
    sort_by: Optional[Literal["id", "status", "created_at"]] = "id",
    order: Optional[Literal["asc", "desc"]] = "desc",
):
    query = select(Order).offset(offset).limit(limit)
    if order == "asc":
        query = query.order_by(asc(sort_by))
    else:
        query = query.order_by(desc(sort_by))
    result = await session.exec(query)
    return result.all()


# UPDATE Order (admin only)
@router.patch(
    "/{order_id}", response_model=OrderRead, dependencies=[Depends(get_admin_user)]
)
async def update_order(
    order_id: uuid.UUID,
    order_in: OrderUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order_in.detail:
        detail = await session.exec(
            select(OrderDetail).where(OrderDetail.order_id == order_id)
        )
        detail = detail.first()
        if detail:
            for k, v in order_in.detail.model_dump(exclude_unset=True).items():
                setattr(detail, k, v)
            session.add(detail)
        else:
            new_detail = OrderDetail(**order_in.detail.model_dump(), order_id=order_id)
            session.add(new_detail)
    if order_in.product_links:
        # Remove old links
        await session.exec(
            select(OrderProductLink)
            .where(OrderProductLink.order_id == order_id)
            .delete()
        )
        # Add new links
        for link in order_in.product_links:
            opl = OrderProductLink(
                order_id=order_id, product_id=link.product_id, quantity=link.quantity
            )
            session.add(opl)
    order.updated_at = datetime.now()
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


# DELETE Order (admin only)
@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_admin_user)],
)
async def delete_order(
    order_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_session)]
):
    order = await session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await session.delete(order)
    await session.commit()
    return None
