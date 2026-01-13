"""
Tests for chat endpoints.
"""
import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_chat_endpoint_requires_auth(client):
    """Test that chat endpoint requires authentication."""
    response = client.post(
        "/chat",
        json={"message": "Hello"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_chat_endpoint_success(client, auth_headers):
    """Test successful chat message."""
    response = client.post(
        "/chat",
        json={"message": "What is my order status?"},
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "response" in data
    assert "intent" in data
    assert "data_source" in data


@pytest.mark.asyncio
async def test_chat_history(client, auth_headers):
    """Test retrieving chat history."""
    # Send a message first
    client.post(
        "/chat",
        json={"message": "Test message"},
        headers=auth_headers
    )

    # Get history
    response = client.get("/chat/history", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["items"][0]["user_message"] == "Test message"


def test_chat_history_requires_auth(client):
    """Test that chat history requires authentication."""
    response = client.get("/chat/history")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
