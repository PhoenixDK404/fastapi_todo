"""Основной файл приложения FastAPI.

Инициализирует FastAPI приложение, создает все таблицы в базе данных
при запуске и подключает рауты для пользователей и задач.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict

from app import models, crud, schemas, auth
from app.auth import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import engine, get_db
from app.routers import users, tasks

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(tasks.router)


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                           db: Session = Depends(get_db)) -> Dict[str, str]:
    """Аутентифицирует пользователя и выдает JWT токен доступа.

    Args:
        form_data (OAuth2PasswordRequestForm): Данные формы с username
                                               и password.
        db (Session, optional): Сессия базы данных.

    Returns:
        dict: Объект с 'access_token' и 'token_type'.
    """
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password,
                                            user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = auth.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username},
                                            expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
