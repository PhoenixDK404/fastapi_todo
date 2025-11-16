"""Модуль тестирования конечных точек API для управления задачами."""

import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app import crud, schemas


def test_create_task_success(client: TestClient, db_session: Session, task_data_generator,
                             authenticated_user_and_token):
    """Тестирует успешное создание задачи аутентифицированным пользователем."""
    user, headers, _ = authenticated_user_and_token
    task_data = task_data_generator()

    response = client.post("/tasks/", json=task_data, headers=headers)

    assert response.status_code == 201

    response_json = response.json()
    assert response_json["title"] == task_data["title"]
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




def test_read_all_tasks_success(client: TestClient, db_session: Session, task_data_generator,
                                authenticated_user_and_token):
    """Тестирует успешное получение списка всех задач."""
    user, _, _ = authenticated_user_and_token

    task1 = crud.create_task(db_session, task=schemas.TaskCreate(**task_data_generator()), user_id=user.id)
    task2 = crud.create_task(db_session, task=schemas.TaskCreate(**task_data_generator()), user_id=user.id)
    db_session.commit()

    response = client.get("/tasks/")

    assert response.status_code == 200
    tasks_list = response.json()
    assert isinstance(tasks_list, list)
    assert len(tasks_list) >= 2

    task_titles = {t['title'] for t in tasks_list}
    assert task1.title in task_titles
    assert task2.title in task_titles


def test_read_task_by_id_success(client: TestClient, db_session: Session, task_data_generator,
                                 authenticated_user_and_token):
    """Тестирует успешное получение задачи по ее ID."""
    user, _, _ = authenticated_user_and_token

    task = crud.create_task(db_session, task=schemas.TaskCreate(**task_data_generator()), user_id=user.id)
    db_session.commit()

    response = client.get(f"/tasks/{task.id}")

    assert response.status_code == 200
    assert response.json()["id"] == task.id
    assert response.json()["owner_id"] == user.id


def test_read_task_not_found(client: TestClient):
    """Тестирует запрос задачи с несуществующим ID."""
    response = client.get("/tasks/99999")

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]




def create_task_fixture(db_session: Session, user_id: int, task_data_generator):
    """Создает и сохраняет новую задачу в БД для указанного пользователя."""
    task = crud.create_task(db_session, task=schemas.TaskCreate(**task_data_generator()), user_id=user_id)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_update_task_success(client: TestClient, db_session: Session, task_data_generator,
                             authenticated_user_and_token):
    """Тестирует успешное обновление задачи ее владельцем."""
    user, headers, _ = authenticated_user_and_token
    task = create_task_fixture(db_session, user.id, task_data_generator)

    update_data = {"description": "Updated description", "status": "finished"}

    response = client.put(f"/tasks/{task.id}", json=update_data, headers=headers)

    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["description"] == update_data["description"]
    assert updated_task["status"] == update_data["status"]


def test_update_task_forbidden(client: TestClient, db_session: Session, task_data_generator,
                               authenticated_user_and_token, another_user_and_token):
    """Тестирует попытку обновления задачи не-владельцем."""
    user1, headers1, _ = authenticated_user_and_token
    user2, _, _ = another_user_and_token

    task_of_user2 = create_task_fixture(db_session, user2.id, task_data_generator)

    update_data = {"description": "Hacked!", "status": "in_progress"}

    response = client.put(f"/tasks/{task_of_user2.id}", json=update_data, headers=headers1)

    assert response.status_code == 403
    assert "Not authorized to update this task" in response.json()["detail"]

    assert crud.get_task(db_session, task_id=task_of_user2.id).description != update_data["description"]


def test_update_task_invalid_status(client: TestClient, db_session: Session, task_data_generator,
                                    authenticated_user_and_token):
    """Тестирует попытку обновления задачи недопустимым значением 'status'."""
    user, headers, _ = authenticated_user_and_token
    task = create_task_fixture(db_session, user.id, task_data_generator)

    update_data = {"status": "invalid_status_value"}

    response = client.put(f"/tasks/{task.id}", json=update_data, headers=headers)

    assert response.status_code == 400
    assert "Invalid status value" in response.json()["detail"]




def test_delete_task_success(client: TestClient, db_session: Session, task_data_generator,
                             authenticated_user_and_token):
    """Тестирует успешное удаление задачи ее владельцем."""
    user, headers, _ = authenticated_user_and_token
    task = create_task_fixture(db_session, user.id, task_data_generator)
    task_id = task.id

    response = client.delete(f"/tasks/{task_id}", headers=headers)

    assert response.status_code == 204

    assert crud.get_task(db_session, task_id=task_id) is None


def test_delete_task_forbidden(client: TestClient, db_session: Session, task_data_generator,
                               authenticated_user_and_token, another_user_and_token):
    """Тестирует попытку удаления задачи не-владельцем."""
    user1, headers1, _ = authenticated_user_and_token
    user2, _, _ = another_user_and_token

    task_of_user2 = create_task_fixture(db_session, user2.id, task_data_generator)

    response = client.delete(f"/tasks/{task_of_user2.id}", headers=headers1)

    assert response.status_code == 403
    assert "Not authorized to delete this task" in response.json()["detail"]

    assert crud.get_task(db_session, task_id=task_of_user2.id) is not None


def test_delete_task_not_found(client: TestClient, authenticated_user_and_token):
    """Тестирует попытку удаления несуществующей задачи."""
    _, headers, _ = authenticated_user_and_token

    response = client.delete("/tasks/99999", headers=headers)

    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]