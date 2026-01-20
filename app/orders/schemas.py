from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, model_validator, EmailStr, Field
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
    prepayment_amount: Optional[Decimal] = None


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


DataT = TypeVar("DataT")


class MerchantData(BaseModel):
    """Дополнительная информация по заявке на стороне провайдера"""

    payment_url: Optional[str] = Field(description="Платежная ссылка", default=None)
    bank_name: Optional[str] = Field(description="Название банка", default=None)
    card_holder_name: Optional[str] = Field(
        description="Имя держателя карты", default=None
    )
    wallet: Optional[str] = Field(
        description="Карта/телефон для депозита", default=None
    )
    currency: Optional[str] = Field(
        description="Валюта оплаты на стороне провайдера", default=None
    )
    amount: Optional[str] = Field(
        description="Сумма в валюте оплаты на стороне провайдера", default=None
    )
    extra_key: Optional[str] = Field(description="Дополнительное поле", default=None)
    rate: Optional[str] = Field(description="Курс", default=None)


class ProviderOrderInfo(BaseModel):
    """Состояние заявки на стороне провайдера"""

    order_id: Optional[int] = Field(description="ID модели Order", default=None)
    provider_order_id: Optional[str] = Field(
        description="ID заявки на стороне провайдера",
        coerce_numbers_to_str=True,
        default=None,
    )
    amount: Optional[Decimal] = Field(
        description="Сумма заявки при создании", default=None, ge=0
    )
    amount_actual: Optional[Decimal] = Field(
        description="Сумма заявки фактическая", default=None, ge=0
    )
    status: Optional[OrderStatus] = Field(description="Статус заявки", default=None)
    merchant_data: Optional[MerchantData] = Field(
        description="Платежная ссылка", default_factory=MerchantData
    )


class SerializedResponse(BaseModel, Generic[DataT]):
    """"""

    success: bool
    raw_data: Optional[Union[dict, list]] = None
    serialized_data: Optional[DataT] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
