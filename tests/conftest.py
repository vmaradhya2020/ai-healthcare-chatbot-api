"""
Pytest configuration and fixtures for Healthcare Chatbot API tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Client, User, UserClient
from app.auth import get_password_hash

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client_data(db_session):
    """
    Create a test client organization in the database.
    """
    client = Client(
        client_code="TEST001",
        name="Test Hospital",
        address="123 Test St",
        contact_email="test@hospital.com",
        contact_phone="555-0100"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture(scope="function")
def test_user(db_session, test_client_data):
    """
    Create a test user with associated client.
    """
    user = User(
        email="testuser@example.com",
        password_hash=get_password_hash("TestPassword123!")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Link user to client
    user_client = UserClient(
        user_id=user.id,
        client_id=test_client_data.id,
        is_primary=1
    )
    db_session.add(user_client)
    db_session.commit()

    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """
    Get authentication headers for a test user.
    """
    response = client.post(
        "/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
