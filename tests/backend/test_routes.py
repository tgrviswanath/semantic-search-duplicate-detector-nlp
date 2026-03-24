import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.core.service.get_stats", new_callable=AsyncMock)
def test_stats_endpoint(mock_stats):
    mock_stats.return_value = {"total_documents": 5, "index_size": 5,
                               "embed_model": "all-MiniLM-L6-v2", "duplicate_threshold": 0.85}
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    assert response.json()["total_documents"] == 5


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
