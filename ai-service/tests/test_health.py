from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_analyze_no_file():
    res = client.post("/api/v1/analyze", data={"session_id": "1"})
    assert res.status_code == 422   # missing 'frame' field