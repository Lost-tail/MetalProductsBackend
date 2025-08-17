from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rub_price: Decimal
    is_active: Optional[bool] = None
    # images: Optional[List[str]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rub_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    images: Optional[List[str]] = None
