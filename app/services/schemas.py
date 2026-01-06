from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel
from enum import Enum


class DeliveryItem(BaseModel):
    quantity: int
    weight: Optional[Decimal] = None
    width: Optional[Decimal] = None
    height: Optional[Decimal] = None
    length: Optional[Decimal] = None
