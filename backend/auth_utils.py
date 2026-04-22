from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
import models

SECRET_KEY = "nortgru-secret-key-2026-nord-ist-group-birobidjan"
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Person: # <--- Заменили User на Person
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise exc
    except InvalidTokenError:
        raise exc

    # Здесь всё верно: ищем в таблице Person
    user = db.query(models.Person).filter(models.Person.email == email).first()
    if user is None:
        raise exc
    return user


def require_role(*roles: str):
    """Dependency-фабрика: проверяет роли пользователя (директор, мастер и т.д.)."""
    def dependency(current_user: models.Person = Depends(get_current_user)):
        # В новой модели роли — это список объектов. Достаем типы ролей.
        user_role_types = [r.role_type for r in current_user.roles]
        
        # Проверяем, есть ли хоть одна подходящая роль
        if not any(role in user_role_types for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав доступа"
            )
        return current_user
    return dependency