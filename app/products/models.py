from typing import List
import uuid
from decimal import Decimal
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(title="Название товара")
    description: str = Field(title="Описание товара", default="")
    rub_price: Decimal = Field(
        title="Цена товара в рублях", max_digits=12, decimal_places=2, gt=0
    )
    images: List[str] = Field(title="Изображения", default_factory=list)
