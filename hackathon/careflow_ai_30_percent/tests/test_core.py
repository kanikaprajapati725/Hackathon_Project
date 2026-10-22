import os
import sys
import tempfile
from pathlib import Path

os.environ["CAREFLOW_DB"] = str(Path(tempfile.mkdtemp()) / "t.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.pipeline import orchestrator  # noqa: E402


def run(text, age=40, vitals=None):
    return orchestrator.run({"code": "T", "patient": {"name": "x", "age": age, "sex": "M"}, "vitals": vitals or {},
                             "created_at": "2026-10-19T10:00:00"}, [{"id": 1, "type": "text", "content": text}])


def test_priority_levels():
    assert run("chest pain and sweating since 1 hour", age=58)["priority"]["level"] == "P1"
    assert run("Papa ko 1 ghante se seene mein dard hai, pasina aa raha hai", age=58)["priority"]["level"] == "P1"
    assert run("4 din se tez bukhar, sar dard")["priority"]["level"] == "P3"
    assert run("mild lower back pain for 2 months")["priority"]["level"] == "P4"
    assert run("routine check, no complaints")["priority"]["level"] == "P5"
    assert run("cough", vitals={"spo2": 88})["priority"]["level"] == "P1"


def test_negation_and_provenance():
    a = run("I have a cough but no fever")
    s = a["facts"]["symptoms"]
    assert s["cough"]["present"] and not s["fever"]["present"]
    ev = s["cough"]["mentions"][0]["evidence"]
    assert "I have a cough but no fever"[ev["start"]:ev["end"]] == ev["quote"]


def test_api_flow():
    with TestClient(app) as c:
        assert c.get("/api/queue").status_code == 401
        tok = c.post("/api/auth/login", json={"username": "nurse.asha", "password": "demo"}).json()["token"]
        h = {"Authorization": "Bearer " + tok}
        code = c.post("/api/cases", headers=h, json={"name": "R", "age": 67, "sex": "F", "language": "en",
                                                     "text": "face drooping and slurred speech since 30 minutes"}).json()["code"]
        assert c.get(f"/api/cases/{code}", headers=h).json()["priority"] == "P1"
        assert c.get("/api/queue", headers=h).json()["cases"][0]["code"] == code
