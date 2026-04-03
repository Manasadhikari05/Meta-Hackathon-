from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_reset_step_task1():
    r = client.post("/reset", params={"task_id": "task1"})
    assert r.status_code == 200
    obs = r.json()
    assert "post" in obs

    r2 = client.post(
        "/step",
        json={
            "decision": "remove",
            "reason_code": "spam",
            "severity": "high",
            "confidence": 0.85,
            "explanation": None,
        },
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["done"] is True
    assert 0.0 <= body["reward"]["value"] <= 1.0
