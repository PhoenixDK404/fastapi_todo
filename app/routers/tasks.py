"""
Маршруты API для управления задачами.

Определяет конечные точки для создания, чтения, обновления и удаления задач,
включая проверку аутентификации пользователя и прав владения задачей.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

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
def read_tasK(task_id: int, db: Session = Depends(get_db)):
    """
        Получает задачу по ее ID.

        Args:
            task_id (int): ID задачи.
            db (Session): Сессия базы данных.

        Returns:
            schemas.Task: Запрошенный объект задачи.
        """
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/{task_id}", response_model=schemas.Task)
def update_tasK(task_id: int, task_data: schemas.TaskUpdate, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    """
        Обновляет существующую задачу по ID.

        Args:
            task_id (int): ID задачи для обновления.
            task_data (schemas.TaskUpdate): Данные для обновления задачи.
            db (Session, optional): Сессия базы данных.
            current_user (models.User): Текущий аутентифицированный пользователь.

        Returns:
            schemas.Task: Обновленный объект задачи.
        """
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")
    updated_task = crud.update_task(db, task_id, task_data, owner_id=current_user.id)  # <-- Добавлено

    if updated_task is None:
        raise HTTPException(status_code=400, detail="Invalid status value")

    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
        Удаляет задачу по ID.

        Args:
            task_id (int): ID задачи для удаления.
            db (Session, optional): Сессия базы данных.
            current_user (models.User): Текущий аутентифицированный пользователь.
        """
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "Not authorized to delete this task")
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return