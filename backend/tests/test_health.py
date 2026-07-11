"""
Smoke test: API health check endpoint
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


def test_health_check():
    """Verify /api/health returns healthy status"""
    from main import app
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_stats_endpoint():
    """Verify /api/stats returns expected keys"""
    from main import app
    client = TestClient(app)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "books" in data
    assert "authors" in data
    assert "schools" in data
    assert isinstance(data["books"], int)
    assert isinstance(data["authors"], int)
    assert isinstance(data["schools"], int)
