"""Pipeline orchestrator - 30% milestone: TEXT PATH ONLY.

Done:   language id (en / Hinglish) -> extraction with provenance -> red-flag rules -> priority + explanation
        -> symptom timeline -> one-line summary.
TODO:   ASR (voice), OCR/report parsing, translation gloss, injection/conflict/quality guards,
        missing-information checks, follow-up questions, draft note, optional SLM. See TODO.md.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

from app.pipeline import extract, redflags
from app.pipeline.text_utils import detect_language

PIPELINE_VERSION = "0.3.0"
VITAL_LABELS = [("spo2", "SpO2", "%"), ("hr", "HR", "/min"), ("sbp", "SBP", "mmHg"), ("temp_c", "Temp", "C")]


def _form_vitals(case: dict) -> tuple[dict | None, list[dict]]:
    v = case.get("vitals") or {}
    text, vitals = "", []
    for key, label, unit in VITAL_LABELS:
        if v.get(key) is None:
            continue
        piece = f"{label}: {v[key]:g} {unit}"
        s = len(text)
        text += piece + "; "
        vitals.append({"name": key, "value": float(v[key]), "evidence": {"segment_id": "F.1", "source_id": "form",
                       "start": s, "end": s + len(piece), "quote": piece}})
    if not text:
        return None, []
    return {"id": "F.1", "source_id": "form", "kind": "form", "text": text.strip(), "lang": "en", "conf": 1.0}, vitals


def run(case: dict, sources: list[dict]) -> dict:
    t0 = time.time()
    segments = []
    form_seg, form_vitals = _form_vitals(case)
    if form_seg:
        segments.append(form_seg)
    skipped = []
    for src in sources:
        if src["type"] != "text":
            skipped.append(src["type"])  # TODO: audio -> ASR (M2), report -> OCR (M3)
            continue
        lang, conf = detect_language(src["content"])
        segments.append({"id": f"S{src['id']}.1", "source_id": src["id"], "kind": "text", "text": src["content"],
                         "lang": lang, "lang_conf": conf, "conf": 1.0})

    per_segment = [(s, extract.extract_segment(s)) for s in segments]
    facts = extract.aggregate(per_segment)
    for v in form_vitals:
        facts["vitals"][v["name"]] = {**v, "source_id": "form"}
    priority = redflags.evaluate(facts, case.get("patient", {}))

    t_sub = datetime.fromisoformat(case.get("created_at") or datetime.now().isoformat(timespec="seconds"))
    timeline = []
    for s in facts["symptoms"].values():
        if s["present"]:
            onset = (t_sub - timedelta(hours=s["duration_hours"])).isoformat(timespec="minutes") if s["duration_hours"] is not None else None
            timeline.append({"label": s["label"], "onset": onset, "duration_hours": s["duration_hours"]})
    timeline.sort(key=lambda x: (x["onset"] is None, x["onset"] or ""))

    present = [s["label"] for s in facts["symptoms"].values() if s["present"]]
    p = case.get("patient", {})
    return {
        "pipeline_version": PIPELINE_VERSION,
        "segments": segments,
        "facts": facts,
        "priority": priority,
        "timeline": timeline,
        "summary": f"{p.get('age', '?')}{(p.get('sex') or '?')[0]}: " + (", ".join(present) or "no active symptoms") +
                   f". Suggested {priority['level']} ({priority['name']}).",
        "not_processed": skipped,
        "timings_ms": {"total": int((time.time() - t0) * 1000)},
    }
