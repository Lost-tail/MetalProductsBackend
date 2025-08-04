#!/usr/bin/env python3
"""
Скрипт для создания первого администратора
"""

import asyncio
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.users.models import User, UserRole
from app.auth.utils import get_password_hash


async def create_admin():
    """Создание администратора"""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Проверяем, есть ли уже админ
        admin = session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
        if admin:
            print("Администратор уже существует!")
            return

        # Создаем админа
        admin_email = input("Введите email администратора: ")
        admin_password = input("Введите пароль администратора: ")

        hashed_password = get_password_hash(admin_password)

        admin_user = User(
            email=admin_email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
        )

        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        print(f"Администратор {admin_email} успешно создан!")


if __name__ == "__main__":
    asyncio.run(create_admin())
