"""Loads the versioned YAML knowledge files once per process."""

from __future__ import annotations

from functools import lru_cache

import yaml

from app.config import KNOWLEDGE_DIR


def _load(name: str) -> dict:
    with open(KNOWLEDGE_DIR / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=None)
def lexicon() -> dict:
    return _load("lexicon.yaml")


@lru_cache(maxsize=None)
def rules() -> dict:
    return _load("redflag_rules.yaml")

# TODO (70%): lab_ranges.yaml, missing_fields.yaml, followups.yaml, consent.yaml
