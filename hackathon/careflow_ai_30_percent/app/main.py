"""CareFlow AI - 30% milestone API.

Done:  demo login, staff text intake, synchronous text pipeline, queue sorted by priority,
       case detail with evidence quotes, simple audit log.
TODO:  patient kiosk + consent, file uploads (voice/report), background worker, RBAC permissions,
       priority override, note editing/approval, flags review, withdraw/erase, FHIR export,
       alerts, ageing, analytics (see TODO.md).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config, db
from app.pipeline import orchestrator
from app.pipeline.redflags import rank

# Demo users. TODO: users table with PBKDF2 password hashes and per-role permissions.
USERS = {"dr.mehta": ("doctor", "Dr. Mehta"), "nurse.asha": ("nurse", "Asha (Triage nurse)"), "intake.ravi": ("intake", "Ravi (Front desk)")}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init()
    yield


app = FastAPI(title="CareFlow AI (30% milestone)", version="0.3.0", lifespan=lifespan)


def _sign(user: str) -> str:
    body = base64.urlsafe_b64encode(user.encode()).decode()
    return body + "." + hmac.new(config.SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()


def current_user(authorization: str | None = Header(default=None)) -> dict:
    try:
        body, sig = (authorization or "")[7:].split(".")
        if hmac.compare_digest(sig, hmac.new(config.SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()):
            u = base64.urlsafe_b64decode(body).decode()
            return {"username": u, "role": USERS[u][0], "name": USERS[u][1]}
    except Exception:
        pass
    raise HTTPException(401, "Not authenticated")


class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginIn):
    if body.username not in USERS or body.password != "demo":
        raise HTTPException(401, "Invalid username or password")
    db.log(body.username, "auth.login")
    role, name = USERS[body.username]
    return {"token": _sign(body.username), "user": {"username": body.username, "role": role, "name": name}}


@app.get("/api/health")
def health():
    return {"ok": True, "milestone": "30%", "engines": {"asr": None, "ocr": None, "slm": None}, "languages": config.LANGUAGES}


class CaseIn(BaseModel):
    name: str | None = None
    age: float | None = None
    sex: str | None = None
    language: str | None = None
    text: str
    vitals: dict[str, float] = {}


def process(code: str) -> dict:
    c = db.get_case(code)
    with db.conn() as cn:
        srcs = [dict(r) for r in cn.execute("SELECT * FROM sources WHERE case_code=? ORDER BY id", (code,)).fetchall()]
    a = orchestrator.run({"code": code, "patient": c["patient"], "language": c["language"], "vitals": c["vitals"],
                          "created_at": c["created_at"]}, srcs)
    with db.conn() as cn:
        cn.execute("UPDATE cases SET analysis_json=?, priority=?, status=?, updated_at=? WHERE code=?",
                   (json.dumps(a, ensure_ascii=False), a["priority"]["level"], "awaiting_review", db.now(), code))
    db.log("ai:careflow-pipeline", "pipeline.completed", code,
           {"priority": a["priority"]["level"], "rules_fired": [r["rule_id"] for r in a["priority"]["red_flags"]]})
    return a


def create_case(body: CaseIn, actor: str, created_at: str | None = None) -> str:
    code = "CF-" + "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(5))
    ts = created_at or db.now()
    age = int(body.age) if body.age is not None and float(body.age).is_integer() else body.age
    patient = {"name": body.name, "age": age, "sex": (body.sex or "")[:1].upper() or None}
    with db.conn() as cn:
        cn.execute("INSERT INTO cases (code, patient_json, language, vitals_json, status, created_at, updated_at, created_by) "
                   "VALUES (?,?,?,?,?,?,?,?)", (code, json.dumps(patient), body.language, json.dumps(body.vitals), "processing", ts, ts, actor))
        cn.execute("INSERT INTO sources (case_code, type, lang, content, created_at) VALUES (?,?,?,?,?)",
                   (code, "text", body.language, body.text, ts))
    db.log(actor, "case.created", code)
    process(code)
    return code


@app.post("/api/cases")
def new_case(body: CaseIn, user: dict = Depends(current_user)):
    if not body.text.strip():
        raise HTTPException(400, "Complaint text is required")
    return {"code": create_case(body, user["username"])}


@app.get("/api/queue")
def queue(user: dict = Depends(current_user)):
    rows = []
    for c in db.list_cases():
        a = c["analysis"] or {}
        rows.append({"code": c["code"], "name": c["patient"].get("name"), "age": c["patient"].get("age"), "sex": c["patient"].get("sex"),
                     "language": c["language"], "priority": c["priority"], "status": c["status"], "created_at": c["created_at"],
                     "summary": a.get("summary"), "red_flags": [r["title"] for r in a.get("priority", {}).get("red_flags", [])][:3]})
    rows.sort(key=lambda r: (rank(r["priority"] or "P3"), r["created_at"]))
    return {"cases": rows}


@app.get("/api/cases/{code}")
def get_case(code: str, user: dict = Depends(current_user)):
    c = db.get_case(code)
    if not c:
        raise HTTPException(404, "Case not found")
    db.log(user["username"], "case.viewed", code)
    return c


@app.get("/")
def root():
    return RedirectResponse("/static/index.html")


app.mount("/static", StaticFiles(directory=config.BASE_DIR / "static"), name="static")
