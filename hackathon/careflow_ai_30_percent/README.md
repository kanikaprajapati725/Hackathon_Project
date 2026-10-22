# CareFlow AI: 30% milestone build

Confluentia 2026 · Tredence Hackathon · Problem Statement 4. This is a snapshot of the project at **~30% completion**. It covers phases 1–2 of the build plan in `../CareFlow_AI_Solution_Reference.pdf`: the skeleton, the data model, and the **text path end to end**.

The finished system is in `../careflow_ai_complete/`. The synthetic dataset is in `../careflow_dataset/`.

## Run it

```bash
cd careflow_ai_30_percent
./run.sh                  # venv + seed 25 supported dataset cases + server on :8001
# open http://localhost:8001  -> sign in as dr.mehta / demo
.venv/bin/python -m pytest -q           # 3 tests
.venv/bin/python -m scripts.evaluate    # text-only evaluation
```

## What works at 30%

| Area | Status |
| --- | --- |
| FastAPI backend + SQLite data model (cases, text sources, audit log) | done |
| Demo staff login (signed token) | done (no per-role permissions yet) |
| Staff text intake: name, age, sex, vitals, complaint (English / Hinglish) | done |
| Language detection (English vs Hinglish) | done |
| **Extraction with provenance**: symptoms, history, negation, durations, severity, trend, vitals, every fact with its exact source span | done |
| **Red-flag rule engine**: 29 versioned YAML rules (ESI / MTS / WHO-ETAT style), P1–P5 priority with explanation and evidence | done |
| Priority-sorted review queue, case view with highlighted evidence, symptom timeline | done |
| Evaluation on the 25 text-only English/Hinglish dataset cases | 24/25 exact. CF-013 (metaphor) is missed by design until the SLM milestone |

## Not built yet (~70%)

See **[TODO.md](TODO.md)** for the full checklist. In short:
- **Inputs:** voice notes (ASR), report OCR and lab parsing.
- **Languages:** Hindi, Tamil and Bengali, plus translation with confidence.
- **Safety checks:** prompt injection, conflicts, unreadable reports, missing-info detection.
- **Clinician workflow:** follow-up questions, draft note with edit/approve/override.
- **Governance:** patient kiosk with consent, withdraw/erase, role-based access, hash-chained audit.
- **Extras:** alerts, queue ageing, FHIR export, analytics, the optional SLM layer.

## Layout

```
app/main.py                 API (login, cases, queue)
app/db.py                   SQLite schema + audit log
app/pipeline/orchestrator.py  text-only pipeline
app/pipeline/extract.py     extraction with provenance      (carried forward unchanged into the complete build)
app/pipeline/redflags.py    rule engine + priority           (carried forward unchanged)
app/pipeline/text_utils.py  normalisation + matching         (carried forward unchanged)
app/knowledge/              lexicon.yaml (EN + Hinglish), redflag_rules.yaml
static/                     index.html + js/app.js (queue, case view, new case)
scripts/evaluate.py         milestone evaluation / seeding
tests/test_core.py
```
