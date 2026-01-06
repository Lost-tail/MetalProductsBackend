from datetime import datetime
from typing import List
import uuid
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from products.models import Product


class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(title="Название категории")
    description: str = Field(title="Описание категории", default="")
    is_active: bool = Field(title="Активен?", default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    products: List["Product"] = Relationship(back_populates="category")
