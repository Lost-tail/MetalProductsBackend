from datetime import datetime
from decimal import Decimal
import os
from typing import Annotated, List, Optional
import aiohttp
from sqlalchemy import or_
from typing_extensions import Literal
import uuid
from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import asc, desc, select
from sqlalchemy.orm import selectinload
from app.db import get_session
from app.services.payment_systems.paykeeper import Paykeeper
from app.settings import settings
from .models import OrderStatus, Product
from . import schemas
from app.auth.dependencies import get_admin_user, get_current_user
from .models import Order, OrderDetail, OrderProductLink
from .schemas import (
    DeliveryPrice,
    OrderCreate,
    OrderRead,
    OrderUpdate,
    RequestForCall,
)
from fastapi_limiter.depends import RateLimiter
from app.services.yandex_delivery import get_yandex_delivery_price
from app.services.schemas import DeliveryItem

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(RateLimiter(times=1, seconds=60))],7
)
async def create_order(
    order_in: OrderCreate, session: Annotated[AsyncSession, Depends(get_session)]
):
    async with session.begin():
        products = (
            await session.exec(
                select(Product).where(
                    Product.id.in_([link.product_id for link in order_in.product_links])
                )
            )
        ).all()
        delivery_items = []
        order_amount = Decimal()
        for product in products:
            quantity = next(
                (
                    link.quantity
                    for link in order_in.product_links
                    if link.product_id == product.id
                ),
                1,
            )
            order_amount += product.rub_price * quantity
            delivery_items.append(
                DeliveryItem(
                    quantity=quantity,
                    weight=product.weight,
                    length=product.length,
                    width=product.width,
                    height=product.height,
                )
            )
        order = Order(amount=order_amount)
        session.add(order)
        await session.flush()
        # Add OrderDetail
        detail = OrderDetail(
            **order_in.detail.model_dump(),
            order_id=order.id,
        )
        if order_in.detail.latitude and order_in.detail.longitude:
            detail.delivery_price = await get_yandex_delivery_price(
                delivery_items=delivery_items,
                latitude=order_in.detail.latitude,
                longitude=order_in.detail.longitude,
            )
        session.add(detail)
        order.detail = detail

        # Add OrderProductLinks
        for link in order_in.product_links:
            opl = OrderProductLink(
                order_id=order.id, product_id=link.product_id, quantity=link.quantity
            )
            session.add(opl)
        payment_system = Paykeeper()
        payment_data = await payment_system.request_deposit(order)
        if payment_data.success:
            order.payment_data = payment_data.serialized_data.merchant_data.model_dump()
            order.external_id = payment_data.serialized_data.provider_order_id
            session.add(order)
        await session.commit()
    await session.refresh(order)
    await session.refresh(order, ["product_links", "detail"])
    return order


@router.get(
    "/{order_id}", response_model=OrderRead, dependencies=[Depends(get_admin_user)]
)
async def get_order(
    order_id: uuid.UUID, session: Annotated[AsyncSession, Depends(get_session)]
):
    order = await session.get(
        Order,
        order_id,
        options=[selectinload(Order.product_links), selectinload(Order.detail)],
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# READ all Orders (anyone)
@router.get("/", response_model=List[OrderRead], dependencies=[Depends(get_admin_user)])
async def get_orders(
    session: Annotated[AsyncSession, Depends(get_session)],
    offset: int = 0,
    limit: int = 100,
    sort_by: Optional[Literal["id", "status", "created_at"]] = "id",
    order: Optional[Literal["asc", "desc"]] = "desc",
):
    query = (
        select(Order)
        .options(selectinload(Order.product_links), selectinload(Order.detail))
        .offset(offset)
        .limit(limit)
    )
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
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    order.updated_at = datetime.now()
    session.add(order)
    await session.commit()
    await session.refresh(order, ["product_links", "detail"])
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
    order = await session.get(
        Order,
        order_id,
        options=[selectinload(Order.product_links), selectinload(Order.detail)],
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await session.delete(order)
    await session.commit()
    return None


@router.post(
    "/request_call",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=1, minutes=30))],
)
async def request_for_call(
    request_for_call: RequestForCall,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if settings.TG_BOT_KEY and settings.TG_CHAT_ID:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"https://api.telegram.org/bot{settings.TG_BOT_KEY}/sendMessage",
                    json={
                        "chat_id": settings.TG_CHAT_ID,
                        "text": f"Новая заявка на звонок от {request_for_call.fio}\nТелефон: `{request_for_call.phone}`\nКомментарий: {request_for_call.comment}",
                        "parse_mode": "MarkDown",
                    },
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        return HTTPException(
                            status_code=500, detail="Failed to send message to Telegram"
                        )
            except Exception as e:
                print("Error sending Telegram message:", e)
                return HTTPException(
                    status_code=500, detail="Failed to send message to Telegram"
                )
    return {"message": "Request for call submitted successfully"}


@router.post(
    "/estimate_delivery",
    status_code=status.HTTP_200_OK,
    response_model=DeliveryPrice,
    dependencies=[Depends(RateLimiter(times=1, seconds=10))],
)
async def estimate_delivery(
    order_in: OrderCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    delivery_items = []
    products = (
        await session.exec(
            select(Product).where(
                Product.id.in_([link.product_id for link in order_in.product_links])
            )
        )
    ).all()
    for product in products:
        quantity = next(
            (
                link.quantity
                for link in order_in.product_links
                if link.product_id == product.id
            ),
            1,
        )
        delivery_items.append(
            DeliveryItem(
                quantity=quantity,
                weight=product.weight,
                length=product.length,
                width=product.width,
                height=product.height,
            )
        )
    return {
        "delivery_price": await get_yandex_delivery_price(
            delivery_items=delivery_items,
            latitude=order_in.detail.latitude,
            longitude=order_in.detail.longitude,
        )
    }


@router.post(f"{settings.WEBHOOK_PREFIX}/payment_webhook", include_in_schema=False)
async def payment_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    request_data = await request.json()
    payment_system = Paykeeper()
    response = None
    if payment_system.check_webhook(request_data):
        callback_data = payment_system.parse_callback_data(request_data)
        order = (
            await session.exec(
                select(Order).where(
                    or_(
                        Order.id == callback_data.order_id,
                        Order.external_id == callback_data.provider_order_id,
                    )
                )
            )
        ).one()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        final_statuses = [
            OrderStatus.PAID,
            OrderStatus.ERROR,
            OrderStatus.CANCELLED,
        ]
        if (
            callback_data.status in final_statuses
            and order.status not in final_statuses
        ):
            order.amount_paid = callback_data.amount_actual
            order.status = OrderStatus.PAID
            session.add(order)
            await session.commit()
            await session.refresh(order)

        response = payment_system.get_callback_response(callback_data.provider_order_id)

    return response or "OK"
