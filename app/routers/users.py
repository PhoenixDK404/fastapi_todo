"""
Маршруты API для управления пользователями.

Определяет конечные точки для создания, чтения, обновления и удаления учетных записей пользователей.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_or_404(user_id: int, db: Session = Depends(get_db)) -> models.User:
    db_user = crud.get_user(db, user_id = user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

def get_authorized_user_for_action(
    target_user: models.User = Depends(get_user_or_404),
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Проверяет, что текущий пользователь является владельцем профиля target_user.
    Если нет, вызывает 403.
    """
    if current_user.id != target_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action on this user"
        )
    return target_user

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
        Создает новую учетную запись пользователя.

        Args:
            user (schemas.UserCreate): Данные для создания пользователя (включая пароль).
            db (Session): Сессия базы данных.

        Returns:
            schemas.User: Созданный объект пользователя.
        """
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=list[schemas.User])
def read_all_users(skip: int = 0, limit: int = 100, db: Session =Depends(get_db)):
    """
        Получает список всех пользователей.

        Args:
            skip (int): Количество пропускаемых записей.
            limit (int): Максимальное количество возвращаемых записей.
            db (Session): Сессия базы данных.

        Returns:
            list[schemas.User]: Список объектов пользователей.
        """
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user: models.User = Depends(get_user_or_404)):
    """Получает пользователя по его ID. """
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user_info(user_data: schemas.UserCreate, user_id: int, target_user: models.User = Depends(get_authorized_user_for_action), db: Session = Depends(get_db)):
    """Обновляет информацию об учетной записи пользователя."""
    updated_user = crud.update_user(db, target_user.id, user_data)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(user_id: int,target_user: models.User = Depends(get_authorized_user_for_action),db: Session = Depends(get_db)):
    """Удаляет учетную запись пользователя."""
    crud.delete_user(db, target_user.id)
    return