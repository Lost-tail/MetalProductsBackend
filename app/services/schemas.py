from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel


class DeliveryItem(BaseModel):
    quantity: int
    cargo_type: Optional[str]
