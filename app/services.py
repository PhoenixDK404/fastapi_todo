"""
Сервисный слой между роутерами и CRUD.

Использование этого слоя обеспечивает чистоту роутеров
и сохраняет CRUD-слой исключительно для операций персистентности.
"""

from sqlalchemy.orm import Session
from app import crud, models, schemas
from fastapi import HTTPException, status
from typing import Optional


def get_task_by_id_for_user(db: Session,
                            task_id: int, user_id: int) -> models.Task:
    """
    Получает задачу по ID, гарантируя,
    что она принадлежит указанному пользователю.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        task_id (int): ID задачи для поиска.
        user_id (int): ID текущего пользователя,
        который должен быть владельцем задачи.

    Returns:
        models.Task: Объект задачи,
        если она найдена и принадлежит пользователю.
    """
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to access this task")
    return db_task


def create_task_for_user(db: Session,
                         task_data: schemas.TaskCreate,
                         user_id: int) -> models.Task:
    """
    Создает задачу в БД, привязывая ее к владельцу.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        task_data (schemas.TaskCreate): Схема Pydantic с данными новой задачи.
        user_id (int): ID пользователя-владельца задачи.

    Returns:
        models.Task: Объект созданной задачи.
    """
    return crud.create_task(db, task_data, user_id)


def update_task_info(db: Session, task_id: int, user_id: int,
                     task_data: schemas.TaskUpdate) -> models.Task:
    """
    Обновляет существующую задачу, гарантируя права доступа.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        task_id (int): ID задачи, которую нужно обновить.
        user_id (int): ID текущего пользователя.
        task_data (schemas.TaskUpdate): Pydantic-схема с данными
                                        для частичного обновления.

    Returns:
        models.Task: Обновленный объект задачи.
    """
    db_task = get_task_by_id_for_user(db, task_id, user_id)
    updated_task = crud.update_task(db, db_task, task_data)
    return updated_task


def delete_task_by_id(db: Session, task_id: int, user_id: int) -> None:
    """
    Удаляет задачу, гарантируя права доступа.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        task_id (int): ID задачи для удаления.
        user_id (int): ID текущего пользователя.

    Returns:
        None
    """
    task_to_delete = get_task_by_id_for_user(db, task_id, user_id)
    crud.delete_task(db, task_to_delete.id)
    return


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Создает нового пользователя в системе.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        user (schemas.UserCreate): Схема Pydantic с данными
                                   нового пользователя.

    Returns:
        models.User: Объект созданного пользователя из БД.
    """
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    return crud.create_user(db=db, user=user)


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Получает пользователя по адресу электронной почты.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        email (str): Адрес электронной почты для поиска.

    Returns:
        Optional[models.User]: Объект пользователя или None, если не найден.
    """
    return crud.get_user_by_email(db, email)


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """
    Получает пользователя по его уникальному ID.

    Args:
        db (Session): Сессия базы данных SQLAlchemy.
        user_id (int): ID пользователя для поиска.

    Returns:
        Optional[models.User]: Объект пользователя или None, если не найден.
    """
    return crud.get_user(db, user_id)
