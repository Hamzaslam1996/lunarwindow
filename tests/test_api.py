from fastapi.testclient import TestClient

from lunarwindow.api.main import app


def test_health_and_reference_sites():
    c = TestClient(app)
    assert c.get("/health").json()["status"] == "ok"
    sites = c.get("/sites/reference").json()
    assert any("Shackleton" in s["name"] for s in sites)
