"""
CRUD операции для взаимодействия с базой данных.

Содержит функции, которые работают с объектами SQLAlchemy Session,
User, и Task, обеспечивая логику доступа и модификации данных.
"""
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash

def get_user(db: Session, user_id: int):
    """
        Получает пользователя по его уникальному ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (int): ID пользователя для поиска.

        Returns:
            Optional[models.User]: Объект пользователя или None, если не найден.
        """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """
        Получает пользователя по его адресу электронной почты.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            email (str): Адрес электронной почты для поиска.

        Returns:
            Optional[models.User]: Объект пользователя или None, если не найден.
        """
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """
        Получает пользователя по его имени пользователя.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            username (str): Имя пользователя для поиска.

        Returns:
            Optional[models.User]: Объект пользователя или None, если не найден.
        """
    return db.query(models.User).filter(models.User.username == username).first()

def get_all_users(db: Session, skip: int =0, limit: int = 100):
    """
        Получает список всех пользователей с возможностью пагинации.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            skip (int): Количество пропускаемых записей.
            limit (int): Максимальное количество возвращаемых записей.

        Returns:
            List[models.User]: Список объектов пользователей.
        """
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """
        Создает нового пользователя в базе данных.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user (schemas.UserCreate): Схема Pydantic с данными пользователя.

        Returns:
            models.User: Объект созданного пользователя.
        """
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_data: schemas.UserCreate):
    """
        Обновляет данные существующего пользователя.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (int): ID пользователя, которого нужно обновить.
            user_data (schemas.UserCreate): Схема Pydantic с новыми данными.

        Returns:
            Optional[models.User]: Обновленный объект пользователя или None, если не найден.
        """
    db_user = get_user(db,user_id)
    if db_user:
        db_user.username = user_data.username
        db_user.email = user_data.email
        if user_data.password:
            db_user.hashed_password = get_password_hash(user_data.password)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def delete_user(db: Session, user_id: int):
    """
        Удаляет пользователя по его ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            user_id (int): ID пользователя для удаления.

        Returns:
            bool: True, если пользователь удален, False, если не найден.
        """
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    """
        Получает список всех задач с возможностью пагинации.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            skip (int): Количество пропускаемых записей.
            limit (int): Максимальное количество возвращаемых записей.

        Returns:
            List[models.Task]: Список объектов задач.
        """
    return db.query(models.Task).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int):
    """
        Получает задачу по ее уникальному ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            task_id (int): ID задачи для поиска.

        Returns:
            Optional[models.Task]: Объект задачи или None, если не найдена.
        """
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    """
        Создает новую задачу в базе данных, привязывая ее к владельцу.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            task (schemas.TaskCreate): Схема Pydantic с данными задачи.
            user_id (int): ID пользователя-владельца задачи.

        Returns:
            models.Task: Объект созданной задачи.
        """
    db_task = models.Task(**task.model_dump(), owner_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_data: schemas.TaskUpdate) -> Optional[models.Task]:
    """
        Обновляет данные существующей задачи, проверяя принадлежность владельцу.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            task_id (int): ID задачи, которую нужно обновить.
            task_data (schemas.TaskUpdate): Схема Pydantic с новыми данными.
            owner_id (int): ID текущего аутентифицированного пользователя (владельца).

        Returns:
            Optional[models.Task]: Обновленный объект задачи или None, если не найдена,
                                   владелец не совпадает, или статус невалиден.
        """
    db_task = get_task(db, task_id)
    if not db_task:
        return None

    task_data_dict = task_data.dict(exclude_unset=True)

    for key, value in task_data_dict.items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    """
        Удаляет задачу по ее ID.

        Args:
            db (Session): Сессия базы данных SQLAlchemy.
            task_id (int): ID задачи для удаления.

        Returns:
            bool: True, если задача удалена, False, если не найдена.
        """
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False