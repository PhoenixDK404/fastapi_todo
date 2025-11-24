# 📌 FastAPI TODO — Backend API

Простой и обучающий проект на **FastAPI**, реализующий функционал управления задачами (To-Do) с поддержкой пользователей, JWT-аутентификации и базой данных.

---

## 📋 Возможности

- Регистрация и авторизация пользователей  
- JWT-токены (логин, защита приватных роутов)  
- CRUD-операции с задачами (создать, получить, изменить, удалить)  
- SQLite (по умолчанию) или возможность подключить другую БД  
- Pydantic-схемы + SQLAlchemy-модели  
- Готовая структура проекта  
- Поддержка тестов через `pytest`  

---
## 📁 Структура проекта
```

fastapi_todo/
├── app/
│ ├── routers/
│ │ ├── tasks.py
│ │ └── users.py
│ ├── init.py
│ ├── auth.py
│ ├── crud.py
│ ├── database.py
│ ├── main.py
│ ├── models.py
│ ├── schemas.py
│ └── services.py
├── tests/
│ ├── init.py
│ ├── conftest.py
│ ├── test_tasks.py
│ └── test_users.py
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── poetry.lock
├── pyproject.toml
└── .env (создаётся пользователем)
```



# ⚙ Настройка проекта

## 1️⃣ Клонирование репозитория

```
git clone https://github.com/PhoenixDK404/fastapi_todo.git
cd fastapi_todo
```

## 2️⃣ Создание файла .env

Создай файл .env в корне проекта и укажите свои данные:

```
DATABASE_URL="sqlite:///./your_database_name.db"

SECRET_KEY="YOUR_OWN_LONG_RANDOM_SECRET_KEY"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 3️⃣ Установка зависимостей
Через Poetry:
```
poetry install
poetry shell
```

## 🚀 Запуск приложения
```
uvicorn app.main:app --reload
```

Открыть:

*Swagger UI: http://localhost:8000/docs

*ReDoc: http://localhost:8000/redoc

## 🧪 Тестирование
```
pytest -v
```

## 🐳 Запуск через Docker
Построить образ:
```
docker build -t fastapi-todo .
```
Запустить контейнер:
```
docker run -d -p 8000:8000 --name fastapi-todo-app fastapi-todo
```
