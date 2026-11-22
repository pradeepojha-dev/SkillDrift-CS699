"""Smoke tests for Pradeep's SkillDrift prototype API."""
from fastapi.testclient import TestClient
from backend import main


def test_health():
    response = TestClient(main.app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_snapshots(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUTS_DIR", tmp_path)
    (tmp_path / "skill_snapshot_2026-10-15.csv").write_text(
        "Date,Skill,Mumbai %,Pune %,Bengaluru %\n2026-10-15,sql,20,30,40\n",
        encoding="utf-8",
    )
    response = TestClient(main.app).get("/api/snapshots")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["snapshots"][0]["rows"][0]["Mumbai %"] == 20.0


def test_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUTS_DIR", tmp_path)
    (tmp_path / "skill_drift_latest.csv").write_text(
        "Skill,Mumbai Change,Mumbai Trend\nsql,12.5,RISING\n", encoding="utf-8"
    )
    response = TestClient(main.app).get("/api/skill-drift")
    assert response.status_code == 200
    assert response.json()["rows"][0]["Mumbai Change"] == 12.5


def test_missing_outputs_returns_503(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUTS_DIR", tmp_path)
    response = TestClient(main.app).get("/api/snapshots")
    assert response.status_code == 503
