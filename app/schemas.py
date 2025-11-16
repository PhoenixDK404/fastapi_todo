"""
Pydantic Схемы данных

Определяет структуры данных для валидации входящих запросов
и форматирования исходящих ответов для сущностей User и Task,
а также для токенов аутентификации.
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional

class TaskBase(BaseModel):
    """Базовая схема для задачи, содержащая поля для создания и обновления."""
    title: str
    description: Optional[str] = None
    status: str = "new"

class TaskCreate(TaskBase):
    """Схема для создания новой задачи (наследует TaskBase)."""
    pass

class TaskUpdate(TaskBase):
    """Схема для частичного обновления существующей задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Task(TaskBase):
    """Схема для чтения задачи"""
    id: int
    owner_id: int
    class Config:
        """Позволяет Pydantic работать с ORM-объектами SQLAlchemy."""
        from_attributes = True

class UserBase(BaseModel):
    """Базовая схема для создания или чтения пользователя"""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """Схема для создания нового пользователя"""
    password: str

class User(UserBase):
    """Схема для чтения пользователя"""
    id: int
    tasks: List[Task] =[]
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Схема для ответа с токеном доступа после успешной аутентификации."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Схема для данных, закодированных в JWT токене"""
    username: Optional[str] = None
