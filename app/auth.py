"""
Логика аутентификации и авторизации, основанная на JWT (JSON Web Tokens).

Содержит утилиты для:
1. Хеширования и проверки паролей.
2. Создания и декодирования JWT токенов.
3. Зависимость FastAPI для получения текущего аутентифицированного пользователя
   из токена в заголовке запроса.
"""

import os

from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import TokenData
from app.models import User as DBUser

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
        Проверяет, соответствует ли открытый пароль хешированному.

        Args:
            plain_password (str): Пароль, введенный пользователем.
            hashed_password (str): Хешированный пароль из базы данных.

        Returns:
            bool: True, если пароли совпадают.
        """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
        Создает хеш для заданного открытого пароля.

        Args:
            password (str): Открытый пароль.

        Returns:
            str: Хешированный пароль.
        """
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Union[str, int]], expires_delta: Optional[timedelta] = None) -> str:
    """
        Создает JWT токен доступа.

        Args:
            data (dict): Данные, которые будут закодированы в JWT (например, 'sub' - subject/username).
            expires_delta (Optional[timedelta]): Срок действия токена.

        Returns:
            str: Сгенерированный JWT токен.
        """
    to_encode: Dict[str, Any] = data.copy()
    if expires_delta:
        expire: datetime = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> DBUser:
    """
        Извлекает и валидирует JWT токен, возвращая объект текущего пользователя.

        Args:
            db (Session, optional): Сессия базы данных.
            token (str, optional): JWT токен, извлеченный из заголовка Authorization.

        Returns:
            DBUser: Объект аутентифицированного пользователя из БД.
        """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user