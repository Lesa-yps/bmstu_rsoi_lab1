# unit тесты для person-service

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

import apiServer
from apiServer import app


# фикстура для тестов: создаёт TestClient и замещает db на MagicMock
@pytest.fixture
def client(monkeypatch):
    mock_db = MagicMock()
    # замена глобального db в модуле apiServer на мок-объект
    monkeypatch.setattr(apiServer, "db", mock_db)
    return TestClient(app), mock_db


# тест на получение списка персон
def test_get_list_persons(client):
    test_client, mock_db = client

    mock_db.fetch_all.return_value = [
        (1, "Ivan", 30, "Moscow", "IT"),
        (2, "Petr", 25, "SPb", "QA"),
    ]

    right_response = [
        {'id': 1, 'name': 'Ivan', 'age': 30, 'address': 'Moscow', 'work': 'IT'},
        {'id': 2, 'name': 'Petr', 'age': 25, 'address': 'SPb', 'work': 'QA'},
    ]

    response = test_client.get("/api/v1/persons")

    assert response.status_code == 200
    assert response.json() == right_response

    mock_db.execute_sql_query.assert_called_once()
    mock_db.fetch_all.assert_called_once()


# тест на создание персоны
def test_create_person(client):
    test_client, mock_db = client

    mock_db.fetch_one.return_value = (42,)

    response = test_client.post(
        "/api/v1/persons",
        json={"name": "Ivan", "age": 30, "address": "Moscow", "work": "IT"},
    )

    assert response.status_code == 201
    assert response.headers["Location"] == "/api/v1/persons/42"
    assert response.content == b"null"

    mock_db.execute_sql_query.assert_called_once()


# тест на получение 1 персоны, когда она есть
def test_get_person(client):
    test_client, mock_db = client

    mock_db.fetch_one.return_value = (1, "Ivan", 30, "Moscow", "IT")

    right_response = {'id': 1, 'name': 'Ivan', 'age': 30, 'address': 'Moscow', 'work': 'IT'}

    response = test_client.get("/api/v1/persons/1")

    assert response.status_code == 200
    assert response.json() == right_response

    mock_db.execute_sql_query.assert_called_once()


# тест на получение 1 персоны, когда её нет
def test_get_person_not_found(client):
    test_client, mock_db = client

    mock_db.fetch_one.return_value = None

    response = test_client.get("/api/v1/persons/999")

    assert response.status_code == 404
    assert response.json()["message"] == "Person not found"


# тест на изменение персоны
def test_edit_person(client):
    test_client, mock_db = client

    mock_db.fetch_one.side_effect = [
        (1,),                                  # 1) проверка, что существует
        (1, "Petr", 30, "Moscow", "IT"),       # 2) после UPDATE
    ]

    response = test_client.patch(
        "/api/v1/persons/1",
        json={"name": "Petr"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Petr"


# тест на удаление персоны
def test_remove_person(client):
    test_client, mock_db = client

    # проверка, что существует
    mock_db.fetch_one.return_value = (1,)

    response = test_client.delete("/api/v1/persons/1")

    assert response.status_code == 204
    assert response.content == b""