"""SQLite persistence - 30% milestone (cases, text sources, simple audit log)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    code TEXT PRIMARY KEY, patient_json TEXT NOT NULL, language TEXT, vitals_json TEXT, status TEXT NOT NULL,
    priority TEXT, analysis_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, created_by TEXT);
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT, case_code TEXT NOT NULL, type TEXT NOT NULL, lang TEXT,
    content TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
    case_code TEXT, detail TEXT);
"""
# TODO (70%): notes, flag_reviews, users table with hashed passwords, consent columns,
#             hash-chained audit (prev_hash/hash), file sources (audio/report paths + sha256).


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def conn():
    c = sqlite3.connect(config.DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)


def _case(r) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("patient_json", "vitals_json", "analysis_json"):
        d[k[:-5]] = json.loads(d.pop(k)) if d.get(k) else None
    return d


def get_case(code: str) -> dict | None:
    with conn() as c:
        return _case(c.execute("SELECT * FROM cases WHERE code=?", (code,)).fetchone())


def list_cases() -> list[dict]:
    with conn() as c:
        return [_case(r) for r in c.execute("SELECT * FROM cases ORDER BY created_at").fetchall()]


def log(actor: str, action: str, case_code: str | None = None, detail: dict | None = None) -> None:
    with conn() as c:
        c.execute("INSERT INTO audit (ts, actor, action, case_code, detail) VALUES (?,?,?,?,?)",
                  (now(), actor, action, case_code, json.dumps(detail or {})))
