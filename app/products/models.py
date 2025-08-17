from datetime import datetime
from typing import List
import uuid
from decimal import Decimal
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(title="Название товара")
    description: str = Field(title="Описание товара", default="")
    rub_price: Decimal = Field(
        title="Цена товара в рублях", max_digits=12, decimal_places=2, gt=0
    )
    is_active: bool = Field(title="Актвен?", default=True)
    images: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
