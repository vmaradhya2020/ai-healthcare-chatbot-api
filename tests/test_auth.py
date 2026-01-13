"""
Tests for authentication endpoints.
"""
import pytest
from fastapi import status


def test_register_user_success(client, test_client_data):
    """Test successful user registration."""
    response = client.post(
        "/register",
        json={
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "client_code": "TEST001"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email fails."""
    response = client.post(
        "/register",
        json={
            "email": "testuser@example.com",  # Already exists
            "password": "Password123!",
            "client_code": "TEST001"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_client_code(client):
    """Test registration with invalid client code fails."""
    response = client.post(
        "/register",
        json={
            "email": "user@example.com",
            "password": "Password123!",
            "client_code": "INVALID999"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "invalid client code" in response.json()["detail"].lower()


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Test login with wrong password fails."""
    response = client.post(
        "/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword!"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user fails."""
    response = client.post(
        "/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, auth_headers):
    """Test getting current user information."""
    response = client.get("/me", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_current_user_no_auth(client):
    """Test getting current user without authentication fails."""
    response = client.get("/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token fails."""
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
