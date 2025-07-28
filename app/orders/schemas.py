from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: Optional[str]
    rub_price: Decimal
    images: Optional[List[str]]


class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    rub_price: Optional[Decimal]
    images: Optional[List[str]]
