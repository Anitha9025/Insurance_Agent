def test_root_endpoint(client):
    """Test the root '/' endpoint returns metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data

def test_health_check_endpoint(client):
    """Test the API v1 health check endpoint '/api/v1/health'."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert "database" in data
    assert "services" in data
    assert "status" in data["database"]
