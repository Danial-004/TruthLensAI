# tests/test_api.py
"""
API Unit Tests for TruthLens AI

This script tests the critical API endpoints of the FastAPI application.
It uses pytest for the testing framework and httpx for asynchronous requests.

To run these tests:
1. Make sure you are in the `backend/` directory.
2. Run the command: pytest -v
"""

import pytest
from httpx import AsyncClient
from backend.app import app # Импортируем наше FastAPI приложение

# --- Pytest Fixtures ---
# Фикстура создает асинхронный клиент для каждого теста,
# гарантируя, что тесты изолированы друг от друга.
@pytest.fixture(scope="module")
async def async_client():
    """Create an async test client for the app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# --- Test Cases ---

# Помечаем тесты как асинхронные, чтобы они работали с async/await
@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """
    Test the /health endpoint.
    It should always return a 200 OK status and indicate a healthy service.
    """
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["model_loaded"] is True
    assert data["database_connected"] is True

@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """
    Test the root / endpoint.
    It should return a welcome message.
    """
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "Welcome to TruthLens AI API" in response.json()["message"]

@pytest.mark.asyncio
async def test_analyze_valid_request_quick_mode(async_client: AsyncClient):
    """
    Test the /analyze endpoint with a valid request in 'quick' mode.
    Expects a successful response with the correct structure.
    """
    payload = {
        "text": "This is a test sentence with enough words to pass the validation check for our API.",
        "mode": "quick"
    }
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "classification" in data
    assert "confidence" in data
    assert "language" in data
    assert "explanation" in data
    assert "sources" in data
    assert "keywords" in data

@pytest.mark.asyncio
async def test_analyze_text_too_short(async_client: AsyncClient):
    """
    Test the /analyze endpoint with text that is too short.
    Expects a 422 Unprocessable Entity error.
    """
    payload = {"text": "Too short.", "mode": "quick"}
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_analyze_missing_text_field(async_client: AsyncClient):
    """
    Test the /analyze endpoint with a missing 'text' field.
    Expects a 422 Unprocessable Entity error.
    """
    payload = {"mode": "quick"}
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_analyze_invalid_mode(async_client: AsyncClient):
    """
    Test the /analyze endpoint with an invalid 'mode' value.
    Expects a 422 Unprocessable Entity error.
    """
    payload = {
        "text": "This is a valid text for testing the mode parameter.",
        "mode": "invalid_mode"
    }
    response = await async_client.post("/analyze", json=payload)
    assert response.status_code == 422