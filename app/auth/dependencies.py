from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from app.db import get_session
from app.users.models import User
from app.auth.utils import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """Получение текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        return None

    email = verify_token(credentials.credentials)
    if email is None:
        return None

    user = (await session.exec(select(User).where(User.email == email))).first()
    if user is None:
        return None

    return user


async def get_admin_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Получение пользователя с ролью админа"""
    if not current_user or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user
