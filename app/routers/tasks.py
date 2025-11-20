"""
Маршруты API для управления задачами.

Определяет конечные точки для создания, чтения, обновления и удаления задач,
включая проверку аутентификации пользователя и прав владения задачей.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.auth import get_current_user
from typing import Annotated

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def get_owned_task_or_fail(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> models.Task:
    """Получает задачу по ID. Если задача не найдена, вызывает 404.
    Если задача найдена, но принадлежит другому пользователю, вызывает 403."""

    db_task = crud.get_task(db, task_id=task_id)

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this task")
    return db_task



@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task_for_current_user(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
        Создает новую задачу и автоматически привязывает ее к текущему аутентифицированному пользователю.

        Args:
            task (schemas.TaskCreate): Данные новой задачи.
            db (Session, optional): Сессия базы данных.
            current_user (models.User): Объект текущего пользователя.

        Returns:
            schemas.Task: Созданный объект задачи.
        """
    return crud.create_task(db=db, task=task, user_id=current_user.id)

@router.get("/", response_model=list[schemas.Task])
def read_all_task(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
        Получает список всех задач.

        Args:
            skip (int): Количество пропускаемых записей.
            limit (int): Максимальное количество возвращаемых записей.
            db (Session): Сессия базы данных.

        Returns:
            list[schemas.Task]: Список задач.
        """
    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
def read_task(task: Annotated[models.Task, Depends(get_owned_task_or_fail)]):
    """
    Получает задачу по ID. Проверяет права доступа.
    """
    return task

@router.put("/{task_id}", response_model=schemas.Task)
def update_task_info(
    task_data: schemas.TaskUpdate,
    task: Annotated[models.Task, Depends(get_owned_task_or_fail)],
    db: Session = Depends(get_db),
):
    """Обновляет существующую задачу по ID"""
    updated_task = crud.update_task(db, task, task_data)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_account(
    task: Annotated[models.Task, Depends(get_owned_task_or_fail)],
    db: Session = Depends(get_db),
):
    """
    Удаляет задачу по ID. Только владелец задачи может ее удалить.
    """
    crud.delete_task(db, task.id)
    return