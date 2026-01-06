from datetime import datetime
import uuid
from enum import Enum
from decimal import Decimal
from sqlmodel import Field, Relationship, SQLModel

from app.products.models import Product


class OrderStatus(str, Enum):
    CREATED = "created"
    CANCELLED = "cancelled"
    PAID = "paid"
    ERROR = "error"
    SUCCESS = "success"


class OrderProductLink(SQLModel, table=True):
    order_id: uuid.UUID = Field(foreign_key="order.id", primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="product.id", primary_key=True)
    quantity: int = Field(title="Количество", gt=0)

    order: "Order" = Relationship(back_populates="product_links")
    product: "Product" = Relationship()


class OrderDetail(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="order.id", unique=True)
    email: str | None = Field(default=None, index=True)
    phone: str | None = Field(default=None, index=True)
    first_name: str | None = Field(default=None)
    address: str | None = Field(default=None)
    latitude: str | None = Field(default=None)
    longitude: str | None = Field(default=None)
    delivery_price: Decimal = Field(
        title="Цена доставки в рублях",
        max_digits=12,
        decimal_places=2,
        ge=0,
        default=0,
    )
    comment: str | None = Field(default=None)

    order: "Order" = Relationship(back_populates="detail")


class Order(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: OrderStatus = Field(
        default=OrderStatus.CREATED,
    )
    product_links: list[OrderProductLink] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete", "passive_deletes": True},
    )
    detail: OrderDetail = Relationship(
        back_populates="order",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        },
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
