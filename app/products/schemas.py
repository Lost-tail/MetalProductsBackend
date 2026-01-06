from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel
from enum import Enum


class CharacteristicIcon(str, Enum):
    ARROW_VERTICAL = "arrow_v"
    ARROW_HORIZONTAL = "arrow_h"
    ARROW_DIAGONAL = "arrow_d"
    LINE_WEIGHT = "line_weight"
    BARBECUE = "barbecue"
    OVEN = "oven"
    ROOF = "roof"


class ProductCharacteristic(BaseModel):
    name: str
    value: Optional[str] = None
    icon: Optional[CharacteristicIcon] = None
    is_main: Optional[bool] = (
        False  # Основная характеристика, которая отображается в карточке товара
    )


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rub_price: Decimal
    is_active: Optional[bool] = None
    is_main: Optional[bool] = None
    characteristics: Optional[List[ProductCharacteristic]] = None
    category_id: Optional[uuid.UUID] = None
    weight: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    length: Optional[Decimal] = None
    # images: Optional[List[str]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rub_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_main: Optional[bool] = None
    images: Optional[List[str]] = None
    characteristics: Optional[List[ProductCharacteristic]] = None
    category_id: Optional[uuid.UUID] = None
    weight: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    length: Optional[Decimal] = None
