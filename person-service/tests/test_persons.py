import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_person():
    r = client.post("/api/v1/persons", json={"name": "Ivan", "age": 30})
    assert r.status_code == 201
    assert "Location" in r.headers


def test_get_person():
    client.post("/api/v1/persons", json={"name": "Ivan"})
    r = client.get("/api/v1/persons/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Ivan"


def test_get_person_not_found():
    r = client.get("/api/v1/persons/999")
    assert r.status_code == 404


def test_update_person():
    client.post("/api/v1/persons", json={"name": "Ivan"})
    r = client.patch("/api/v1/persons/1", json={"name": "Petr"})
    assert r.status_code == 200
    assert r.json()["name"] == "Petr"


def test_delete_person():
    client.post("/api/v1/persons", json={"name": "Ivan"})
    r = client.delete("/api/v1/persons/1")
    assert r.status_code == 204