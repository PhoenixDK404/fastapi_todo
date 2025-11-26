"""SQLAlchemy Модели для базы данных.

Определяет структуру таблиц 'users' и 'tasks', их поля, ключи и взаимосвязи
для ORM.
"""

from typing import List
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.types import Enum as SqlEnum
from app.database import Base
from app.schemas import TaskStatus


class User(Base):
    """Модель базы данных для пользователя.

    Attributes:
        __tablename__ (str): Имя таблицы в БД ("users").
        id (int): Первичный ключ, уникальный идентификатор пользователя.
        username (str): Уникальное имя пользователя.
        email (str): Уникальный адрес электронной почты.
        hashed_password (str): Хеш пароля пользователя.
        tasks (relationship): Связь с Task, принадлежащие этому пользователю.
    """

    __tablename__ = "users"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    username: Mapped[str] = Column(String(50), index=True, unique=True)
    email: Mapped[str] = Column(String(100), index=True, unique=True)
    hashed_password: Mapped[str] = Column(String(128))
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="owner")


class Task(Base):
    """Модель базы данных для задач.

    Attributes:
        __tablename__ (str): Имя таблицы в БД ("tasks").
        id (int): Первичный ключ, уникальный идентификатор задачи.
        title (str): Название задачи.
        description (str): Полное описание задачи.
        status (str): Текущий статус задачи (по умолчанию "new").
        owner_id (int): Внешний ключ, ID пользователя-владельца.
        owner (relationship): Связь с моделью User (владелец задачи).
    """

    __tablename__ = "tasks"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String(100), index=True)
    description: Mapped[str] = Column(String(500), nullable=True)
    status: Mapped[TaskStatus] = Column(SqlEnum(TaskStatus),
                                        default=TaskStatus.new)
    owner_id: Mapped[int] = Column(Integer, ForeignKey("users.id"))
    owner: Mapped["User"] = relationship("User", back_populates="tasks")
