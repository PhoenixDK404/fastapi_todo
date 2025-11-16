"""
SQLAlchemy Модели для базы данных.

Определяет структуру таблиц 'users' и 'tasks', их поля, ключи и взаимосвязи
для ORM.
"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """
        Модель базы данных для пользователя.

        Attributes:
            __tablename__ (str): Имя таблицы в БД ("users").
            id (int): Первичный ключ, уникальный идентификатор пользователя.
            username (str): Уникальное имя пользователя.
            email (str): Уникальный адрес электронной почты.
            hashed_password (str): Хеш пароля пользователя.
            tasks (relationship): Связь с моделью Task, принадлежащие этому пользователю.
        """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)
    email = Column(String, index=True, unique=True)
    hashed_password = Column(String)
    tasks = relationship("Task", back_populates="owner")

class Task(Base):
    """
        Модель базы данных для задач.

        Attributes:
            __tablename__ (str): Имя таблицы в БД ("tasks").
            id (int): Первичный ключ, уникальный идентификатор задачи.
            title (str): Название задачи.
            description (str, optional): Полное описание задачи (может быть None).
            status (str): Текущий статус задачи (по умолчанию "new").
            owner_id (int): Внешний ключ, ID пользователя-владельца.
            owner (relationship): Связь с моделью User (владелец задачи).
        """
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="new")
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tasks")