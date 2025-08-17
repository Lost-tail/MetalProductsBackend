from datetime import datetime, timedelta
import os
from typing import Optional
from fastapi import UploadFile
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.settings import settings

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


async def download_file(file: UploadFile, dir: str) -> str:
    os.makedirs(dir, exist_ok=True)

    # Генерируем путь для сохранения
    file_location = os.path.join(dir, file.filename)

    # Сохраняем файл
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    return file_location


async def remove_file(path: str) -> str:
    try:
        os.remove(path.replace(f"{settings.SERVER_HOST}/", ""))
    except Exception as e:
        print(f"Error when deleting file {path}\n{e}")
