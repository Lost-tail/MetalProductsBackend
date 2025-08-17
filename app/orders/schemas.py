from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, model_validator, EmailStr
import uuid

from .models import OrderStatus


class OrderDetailBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: str
    last_name: str
    address: str
    comment: Optional[str] = ""

    @model_validator(mode="after")
    def email_or_phone_required(self, values):
        email, phone = values.get("email"), values.get("phone")
        if not email and not phone:
            raise ValueError("Either email or phone must be provided")
        return values


class OrderDetailCreate(OrderDetailBase):
    pass


class OrderDetailRead(OrderDetailBase):
    id: uuid.UUID
    order_id: uuid.UUID

    class Config:
        from_attributes = True


class OrderProductLinkBase(BaseModel):
    product_id: uuid.UUID
    quantity: int


class OrderProductLinkCreate(OrderProductLinkBase):
    pass


class OrderProductLinkRead(OrderProductLinkBase):
    pass


class OrderBase(BaseModel):
    pass


class OrderCreate(OrderBase):
    product_links: List[OrderProductLinkCreate]
    detail: OrderDetailCreate


class OrderRead(OrderBase):
    id: uuid.UUID
    status: OrderStatus
    product_links: List[OrderProductLinkRead]
    detail: Optional[OrderDetailRead]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderUpdate(OrderBase):
    product_links: Optional[List[OrderProductLinkCreate]] = None
    detail: Optional[OrderDetailCreate] = None
    status: Optional[OrderStatus] = None
