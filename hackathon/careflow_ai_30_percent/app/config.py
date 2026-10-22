"""Runtime configuration - 30% milestone."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "app" / "knowledge"
DATA_DIR = Path(os.environ.get("CAREFLOW_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.environ.get("CAREFLOW_DB", DATA_DIR / "careflow.db"))
DATASET_DIR = Path(os.environ.get("CAREFLOW_DATASET", BASE_DIR.parent / "careflow_dataset"))
SECRET_KEY = os.environ.get("CAREFLOW_SECRET", "dev-only-change-me")

# Supported in this milestone. TODO: hi, ta, bn (see TODO.md, milestone M4).
LANGUAGES = {"en": "English", "hi-en": "Hinglish"}

DATA_DIR.mkdir(parents=True, exist_ok=True)
