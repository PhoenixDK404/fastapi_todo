"""Модуль тестирования конечных точек API для управления задачами."""

import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Callable, Dict, Tuple
from app import crud, models


def test_create_task_success(client: TestClient, db_session: Session, task_data_generator,
                             authenticated_user_and_token):
    """Тестирует успешное создание задачи аутентифицированным пользователем."""
    user, headers, _ = authenticated_user_and_token
    task_data = task_data_generator()

    response = client.post("/tasks/", json=task_data, headers=headers)

    assert response.status_code == 201

    response_json = response.json()
    assert response_json["title"] == task_data["title"]
    assert response_json["description"] == task_data["description"]
    assert response_json["owner_id"] == user.id

    db_task = crud.get_task(db_session, task_id=response_json["id"])
    assert db_task is not None
    assert db_task.owner_id == user.id


def test_create_task_unauthorized(client: TestClient, task_data_generator):
    """Тестирует попытку создания задачи без токена аутентификации."""
    task_data = task_data_generator()
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_read_all_tasks_success(client: TestClient, task_factory: Callable,
                                authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное получение списка задач и проверяет их содержимое."""
    user1, headers1, _ = authenticated_user_and_token

    task1 = task_factory(user1.id, initial_data={"title": "User1 Task 1"})
    task2 = task_factory(user1.id, initial_data={"title": "User1 Task 2"})

    response = client.get("/tasks/", headers=headers1)
    assert response.status_code == 200

    tasks = response.json()
    assert len(tasks) == 2

    task_titles = {t['title'] for t in tasks}
    assert task1.title in task_titles
    assert task2.title in task_titles

    for task in tasks:
        assert task["owner_id"] == user1.id


def test_read_task_by_id_success(client: TestClient, task_factory: Callable, authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное получение задачи по ID."""
    user, headers, _ = authenticated_user_and_token
    task = task_factory(user.id)

    response = client.get(f"/tasks/{task.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == task.id
    assert response.json()["title"] == task.title

def test_read_task_not_found(client: TestClient):
    """Тестирует запрос задачи с несуществующим ID."""
    response = client.get("/tasks/99999")

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_task_success(client: TestClient, db_session: Session, task_factory: Callable,
                             authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное обновление задачи."""
    user, headers, _ = authenticated_user_and_token
    task = task_factory(user.id)

    update_data = {"description": "Updated description", "status": "finished"}

    response = client.put(f"/tasks/{task.id}", json=update_data, headers=headers)
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["description"] == update_data["description"]
    assert response_json["status"] == "finished"

    db_task = crud.get_task(db_session, task_id=task.id)
    assert db_task.description == update_data["description"]
    assert db_task.status.value == "finished"


def test_update_task_forbidden(client: TestClient, db_session: Session, task_factory: Callable,
                               authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]],
                               another_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует попытку обновления задачи не-владельцем. Ожидаем 403."""
    user1, headers1, _ = authenticated_user_and_token
    user2, _, _ = another_user_and_token

    task_of_user2 = task_factory(user2.id)
    initial_description = task_of_user2.description

    update_data = {"description": "Attempted forbidden update"}

    response = client.put(f"/tasks/{task_of_user2.id}", json=update_data, headers=headers1)

    assert response.status_code == 403
    assert "Not authorized to update this task" in response.json()["detail"]

    db_task_after = crud.get_task(db_session, task_id=task_of_user2.id)
    assert db_task_after.description == initial_description


def test_update_task_invalid_status(client: TestClient, db_session: Session, task_factory: Callable,
                                    authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует попытку обновления задачи недопустимым значением 'status'. Ожидаем 422."""
    user, headers, _ = authenticated_user_and_token
    task = task_factory(user.id)

    update_data = {"status": "invalid_status_value"}

    response = client.put(f"/tasks/{task.id}", json=update_data, headers=headers)

    assert response.status_code == 422
    response_json = response.json()
    assert "Input should be 'new', 'in processing' or 'finished'" in response_json["detail"][0]["msg"]


def test_delete_task_success(client: TestClient, db_session: Session, task_factory: Callable, authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует успешное удаление задачи."""
    user, headers, _ = authenticated_user_and_token
    task = task_factory(user.id)

    response = client.delete(f"/tasks/{task.id}", headers=headers)
    assert response.status_code == 204

    db_task = crud.get_task(db_session, task_id=task.id)
    assert db_task is None

def test_delete_task_forbidden(client: TestClient, db_session: Session, task_factory: Callable,
                               authenticated_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]],
                               another_user_and_token: Tuple[models.User, Dict[str, str], Dict[str, str]]):
    """Тестирует попытку удаления задачи не-владельцем."""
    user1, headers1, _ = authenticated_user_and_token
    user2, _, _ = another_user_and_token

    task_of_user2 = task_factory(user2.id)

    response = client.delete(f"/tasks/{task_of_user2.id}", headers=headers1)
    assert response.status_code == 403
    assert "Not authorized to delete this task" in response.json()["detail"]

    db_task = crud.get_task(db_session, task_id=task_of_user2.id)
    assert db_task is not None

def test_delete_task_not_found(client: TestClient, authenticated_user_and_token):
    """Тестирует попытку удаления несуществующей задачи."""
    _, headers, _ = authenticated_user_and_token

    response = client.delete("/tasks/99999", headers=headers)

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]