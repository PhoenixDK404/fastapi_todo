"""
Маршруты API для управления задачами.

Определяет конечные точки для создания, чтения, обновления и удаления задач,
включая проверку аутентификации пользователя и прав владения задачей.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app import crud, schemas, models, services
from app.database import get_db
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/",
    response_model=schemas.Task,
    status_code=status.HTTP_201_CREATED
)
def create_task_for_current_user(
        task: schemas.TaskCreate, db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)) -> models.Task:
    """
        Создает новую задачу и автоматически привязывает ее к
        текущему аутентифицированному пользователю.

        Args:
            task (schemas.TaskCreate): Данные новой задачи.
            db (Session, optional): Сессия базы данных.
            current_user (models.User): Объект текущего пользователя.

        Returns:
            schemas.Task: Созданный объект задачи.
        """
    return services.create_task_for_user(db=db,
                                         task_data=task,
                                         user_id=current_user.id)


@router.get("/", response_model=list[schemas.Task])
def read_all_task(skip: int = 0, limit: int = 100,
                  db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user))\
                 -> List[models.Task]:
    """
        Получает список всех задач.

        Args:
            skip (int): Количество пропускаемых записей.
            limit (int): Максимальное количество возвращаемых записей.
            db (Session): Сессия базы данных.

        Returns:
            list[schemas.Task]: Список задач.
        """
    tasks = crud.get_tasks(db,
                           owner_id=current_user.id,
                           skip=skip, limit=limit)
    return tasks


@router.get("/{task_id}", response_model=schemas.Task)
def read_task(task_id: int,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)) \
              -> models.Task:
    """
    Получает задачу по ID. Проверяет права доступа.
    """
    return services.get_task_by_id_for_user(db, task_id, current_user.id)


@router.put("/{task_id}", response_model=schemas.Task)
def update_task_info(task_id: int,
                     task_data: schemas.TaskUpdate,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)) \
                     -> models.Task:
    """Обновляет существующую задачу по ID"""
    updated_task = services.update_task_info(db,
                                             task_id,
                                             current_user.id, task_data)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_account(task_id: int,
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user),
                        ) -> None:
    """
    Удаляет задачу по ID. Только владелец задачи может ее удалить.
    """
    services.delete_task_by_id(db, task_id, current_user.id)
    return
