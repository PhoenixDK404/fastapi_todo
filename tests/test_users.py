"""Модуль тестирования конечных точек API для управления пользователями."""

from typing import Callable, Dict, Tuple
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app import crud, schemas, models


def test_create_user_success(client: TestClient,
                             user_data_generator: Callable[[], Dict[str, str]],
                             db_session: Session):
    """Тестирует успешное создание нового пользователя."""
    data = user_data_generator()

    response = client.post("/users/", json=data)

    assert response.status_code == 201

    db_user = crud.get_user_by_username(db_session, username=data["username"])
    assert db_user is not None
    assert db_user.email == data["email"]
    assert "hashed_password" not in response.json()


def test_create_user_duplicate_email_fail(
    client: TestClient,
    user_data_generator: Callable[[], Dict[str, str]],
    db_session: Session,
):
    """Тестирует, что создание пользователя завершается ошибкой
    при дублировании email."""
    data_original = user_data_generator()
    crud.create_user(db_session, schemas.UserCreate(**data_original))
    db_session.commit()

    data_duplicate = user_data_generator()
    data_duplicate["email"] = data_original["email"]

    response = client.post("/users/", json=data_duplicate)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_create_user_duplicate_username_fail(
        client: TestClient,
        user_data_generator: Callable[[], Dict[str, str]],
        db_session: Session):
    """Тестирует, что создание пользователя завершается ошибкой
    при дублировании username."""
    data_original = user_data_generator()
    crud.create_user(db_session, schemas.UserCreate(**data_original))
    db_session.commit()

    data_duplicate = user_data_generator()
    data_duplicate["username"] = data_original["username"]

    response = client.post("/users/", json=data_duplicate)

    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]


def test_read_all_users_success(
        client: TestClient,
        db_session: Session,
        user_data_generator: Callable[[], Dict[str, str]]):
    """Тестирует успешное получение списка всех пользователей."""
    user_data_1 = user_data_generator()
    user_data_2 = user_data_generator()
    crud.create_user(db_session, schemas.UserCreate(**user_data_1))
    crud.create_user(db_session, schemas.UserCreate(**user_data_2))
    db_session.commit()

    response = client.get("/users/")

    assert response.status_code == 200
    users_list = response.json()
    assert isinstance(users_list, list)
    assert len(users_list) >= 2


def test_read_user_by_id_success(
        client: TestClient,
        db_session: Session,
        user_data_generator: Callable[[], Dict[str, str]]):
    """Тестирует успешное получение пользователя по его ID."""
    data = user_data_generator()
    created_user = crud.create_user(db_session, schemas.UserCreate(**data))
    db_session.commit()

    response = client.get(f"/users/{created_user.id}")

    assert response.status_code == 200
    assert response.json()["id"] == created_user.id
    assert response.json()["email"] == data["email"]


def test_read_user_not_found(client: TestClient):
    """Тестирует запрос несуществующего пользователя."""
    response = client.get("/users/99999")

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_update_user_info_success(
        client: TestClient,
        db_session: Session,
        authenticated_user_and_token:
        Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное обновление данных своего аккаунта
    аутентифицированным пользователем."""

    created_user, headers, _ = authenticated_user_and_token

    update_data = {
        "username": "new_name",
        "email": "new_email@test.com",
        "password": "new_password123"
    }

    response = client.put(f"/users/{created_user.id}",
                          json=update_data, headers=headers)

    assert response.status_code == 200
    updated_user_data = response.json()
    assert updated_user_data["username"] == update_data["username"]
    assert updated_user_data["email"] == update_data["email"]


def test_update_user_info_forbidden(
        client: TestClient,
        db_session: Session,
        user_data_generator: Callable[[], Dict[str, str]],
        authenticated_user_and_token:
        Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует, что аутентифицированный пользователь не может
    обновлять чужой аккаунт."""
    _, headers, _ = authenticated_user_and_token

    user_data_2 = user_data_generator()
    user_2 = crud.create_user(db_session, schemas.UserCreate(**user_data_2))
    db_session.commit()

    update_data = {"username": "hacker_name",
                   "email": "hacker@test.com",
                   "password": "pass"}

    response = client.put(f"/users/{user_2.id}",
                          json=update_data, headers=headers)

    assert response.status_code == 403
    assert ("Not authorized to perform this action on this user"
            in response.json()["detail"])


def test_update_user_info_unauthorized(
        client: TestClient,
        db_session: Session,
        user_data_generator: Callable[[], Dict[str, str]]):
    """Тестирует, что неаутентифицированный пользователь не может
    обновлять аккаунт."""
    data = user_data_generator()
    user = crud.create_user(db_session, schemas.UserCreate(**data))
    db_session.commit()

    update_data = {"username": "anon_name",
                   "email": "anon@test.com", "password": "pass"}

    response = client.put(f"/users/{user.id}", json=update_data)

    assert response.status_code == 401


def test_delete_user_self_success(
        client: TestClient,
        db_session: Session,
        authenticated_user_and_token:
        Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное удаление пользователем своего аккаунта."""
    created_user, headers, _ = authenticated_user_and_token
    user_id = created_user.id

    response = client.delete(f"/users/{user_id}", headers=headers)

    assert response.status_code == 204
    assert crud.get_user(db_session, user_id=user_id) is None


def test_delete_user_other_fail(
        client: TestClient,
        db_session: Session,
        user_data_generator: Callable[[], Dict[str, str]],
        authenticated_user_and_token:
        Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует, что аутентифицированный пользователь не может
    удалить чужой аккаунт."""
    _, headers, _ = authenticated_user_and_token

    user_data_2 = user_data_generator()
    user_2 = crud.create_user(db_session, schemas.UserCreate(**user_data_2))
    db_session.commit()

    response = client.delete(f"/users/{user_2.id}", headers=headers)

    assert response.status_code == 403
    assert ("Not authorized to perform this action on this user"
            in response.json()["detail"])

    assert crud.get_user(db_session, user_id=user_2.id) is not None
