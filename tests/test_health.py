"""
Tests for health check endpoints.
"""
from fastapi import status


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


def test_liveness_check(client):
    """Test liveness check endpoint."""
    response = client.get("/health/live")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_check(client):
    """Test readiness check endpoint."""
    response = client.get("/health/ready")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] is True
