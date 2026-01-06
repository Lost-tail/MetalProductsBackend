from datetime import datetime
from typing import Optional
import uuid
from decimal import Decimal
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON
from .schemas import ProductCharacteristic

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from categories.models import Category


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(title="Название товара")
    description: str = Field(title="Описание товара", default="")
    rub_price: Decimal = Field(
        title="Цена товара в рублях", max_digits=12, decimal_places=2, gt=0
    )
    is_active: bool = Field(title="Активен?", default=True)
    is_main: bool = Field(title="Отображать на главно?", default=False)
    images: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    characteristics: list[ProductCharacteristic] = Field(
        default_factory=list, sa_column=Column(JSON)
    )
    weight: Optional[Decimal] = Field(title="Вес товара", default=Decimal("0.0"))
    width: Optional[Decimal] = Field(
        title="Ширина товара, в метрах", default=Decimal("0.0")
    )
    height: Optional[Decimal] = Field(
        title="Высота товара, в метрах", default=Decimal("0.0")
    )
    length: Optional[Decimal] = Field(
        title="Длина товара, в метрах", default=Decimal("0.0")
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    category_id: Optional[uuid.UUID] = Field(foreign_key="category.id", default=None)
    category: "Category" = Relationship(back_populates="products")
