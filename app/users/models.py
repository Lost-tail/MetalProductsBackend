from enum import Enum
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.CLIENT)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
