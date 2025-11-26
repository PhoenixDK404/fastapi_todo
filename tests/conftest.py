"""Конфигурация Pytest для тестовой среды приложения.

Содержит фикстуры для настройки базы данных, клиента FastAPI
и управления аутентифицированными пользователями и токенами доступа.
"""
import pytest
from sqlalchemy import Engine
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, engine, get_db, SessionLocal
from app import crud, schemas, models
from typing import Callable, Dict, Any, Tuple, Generator, Optional


@pytest.fixture(scope="session")
def user_data_generator() -> Callable[[], Dict[str, str]]:
    """Функция для генерации уникальных тестовых данных пользователя."""
    counter = 0

    def _generator():
        nonlocal counter
        counter += 1
        return {
            "username": f"testuser_{counter}",
            "email": f"test_{counter}@example.com",
            "password": "testpassword123"
        }

    return _generator


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Настраивает тестовый движок базы данных."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Engine, None, None]:
    """Создает изолированную сессию базы данных для каждого теста.

    Args:
        db_engine (Engine): Фикстура движка БД.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield db

    transaction.rollback()
    connection.close()
    app.dependency_overrides = {}


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Предоставляет тестовый клиент для взаимодействия с приложением."""
    with TestClient(app, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
def get_auth_token_fixture(client: TestClient) -> Callable[[str, str], str]:
    """Фабрика для получения JWT токена доступа.

    Args:
        client (TestClient): Фикстура тестового клиента.

    Returns:
        function: Функция, принимающая username и password
                  и возвращающая токен.
    """

    def _get_auth_token(username, password) -> str:

        response = client.post(
            "/token",
            data={"username": username, "password": password}
        )

        assert response.status_code == 200, \
            f"Failed to get token: {response.json()}"
        return response.json()["access_token"]

    return _get_auth_token


@pytest.fixture(scope="function")
def authenticated_user_and_token(db_session: Session,
                                 user_data_generator:
                                 Callable[[], Dict[str, str]],
                                 get_auth_token_fixture:
                                 Callable[[str, str], str]) \
        -> Tuple[models.User, Dict[str, str], Dict[str, str]]:
    """Создает нового пользователя в БД и немедленно аутентифицирует его.

    Args:
        db_session (Session): Фикстура сессии БД.
        user_data_generator (function): Фабрика для генерации
                                        данных пользователя.
        get_auth_token_fixture (function): Фабрика для получения токена.

    Returns:
        tuple: (
            models.User: Объект созданного пользователя,
            dict: Заголовок авторизации ({"Authorization": "Bearer <token>"}),
            dict: Исходные данные пользователя (username, email, password)
        )
    """
    user_data = user_data_generator()

    user = crud.create_user(db_session, schemas.UserCreate(**user_data))

    db_session.commit()
    db_session.refresh(user)

    token = get_auth_token_fixture(user_data["username"],
                                   user_data["password"])

    return user, {"Authorization": f"Bearer {token}"}, user_data


@pytest.fixture(scope="session")
def task_data_generator() -> Callable[[], Dict[str, str]]:
    """Фабрика для генерации уникальных тестовых данных задачи."""
    counter = 0

    def _generator():
        nonlocal counter
        counter += 1
        return {
            "title": f"Test Task Title {counter}",
            "description": f"Details for task {counter}",
            "status": schemas.TaskStatus.new.value
        }

    return _generator


@pytest.fixture(scope="function")
def task_factory(db_session: Session,
                 task_data_generator: Callable[[], Dict[str, Any]]) \
        -> Callable[[int, Optional[Dict[str, Any]]], models.Task]:
    """Фикстура для создания и сохранения объекта Task в БД."""
    def _create_task(owner_id: int,
                     initial_data: Dict[str, Any] = None) -> models.Task:
        data = task_data_generator()
        if initial_data:
            data.update(initial_data)
        task_schema = schemas.TaskCreate(**data)
        return crud.create_task(db=db_session,
                                task=task_schema,
                                user_id=owner_id)  # type: ignore

    return _create_task


@pytest.fixture(scope="function")
def another_user_and_token(db_session: Session,
                           user_data_generator:
                           Callable[[], Dict[str, str]],
                           get_auth_token_fixture:
                           Callable[[str, str], str]) \
        -> Tuple[models.User, Dict[str, str], Dict[str, str]]:
    """Создает второго, независимого пользователя.

    Args:
        db_session (Session): Фикстура сессии БД.
        user_data_generator (function): Фабрика для генерации
                                        данных пользователя.
        get_auth_token_fixture (function): Фабрика для получения токена.

    Returns:
        tuple: (
            models.User: Объект созданного пользователя,
            dict: Заголовок авторизации,
            dict: Исходные данные пользователя
        )
    """
    user_data = user_data_generator()

    user = crud.create_user(db_session, schemas.UserCreate(**user_data))

    db_session.commit()
    db_session.refresh(user)

    token = get_auth_token_fixture(user_data["username"],
                                   user_data["password"])

    return user, {"Authorization": f"Bearer {token}"}, user_data
