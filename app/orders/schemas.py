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
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    comment: Optional[str] = ""

    @model_validator(mode="after")
    def email_or_phone_required(self, values):
        email, phone = self.email, self.phone
        if not email and not phone:
            raise ValueError("Either email or phone must be provided")
        return self

    @model_validator(mode="after")
    def coordinates_validation(self, values):
        if not self.latitude or not self.longitude:
            return self
        try:
            latitude, longitude = float(self.latitude), float(self.longitude)
        except ValueError:
            raise ValueError("Latitude and Longitude must be valid float numbers")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Longitude {longitude} must be between -180 and 180")
        if not -90 <= latitude <= 90:
            raise ValueError(f"Latitude {latitude} must be between -90 and 90")
        return self


class OrderDetailCreate(OrderDetailBase):
    pass


class OrderDetailRead(OrderDetailBase):
    id: uuid.UUID
    order_id: uuid.UUID
    delivery_price: Optional[Decimal] = None

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
    # product_links: Optional[List[OrderProductLinkCreate]] = None
    # detail: Optional[OrderDetailCreate] = None
    status: Optional[OrderStatus] = None


class RequestForCall(BaseModel):
    phone: str
    fio: str
    comment: Optional[str] = ""


class DeliveryPrice(BaseModel):
    delivery_price: Decimal
