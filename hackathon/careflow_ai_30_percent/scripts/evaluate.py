"""Milestone evaluation: text-only English/Hinglish cases from the synthetic dataset.

  python -m scripts.evaluate           # evaluate supported cases
  python -m scripts.evaluate --seed    # also load them into the app database
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, db  # noqa: E402
from app.pipeline import orchestrator  # noqa: E402
from app.pipeline.redflags import LEVELS  # noqa: E402


def supported(c: dict) -> bool:
    return all(i["type"] == "text" and i.get("lang") in config.LANGUAGES for i in c["inputs"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(config.DATASET_DIR))
    ap.add_argument("--seed", action="store_true")
    args = ap.parse_args()
    cases = json.loads((Path(args.dataset) / "cases.json").read_text(encoding="utf-8"))
    sup = [c for c in cases if supported(c)]
    print(f"{len(sup)}/{len(cases)} cases are text-only English/Hinglish (supported in this milestone)\n")
    exact = under = 0
    for c in sup:
        case = {"code": c["case_id"], "patient": c["patient"], "language": c["language"], "vitals": c.get("vitals") or {},
                "created_at": "2026-10-19T10:00:00"}
        a = orchestrator.run(case, [{"id": i, **inp} for i, inp in enumerate(c["inputs"], 1)])
        pred, gold = a["priority"]["level"], c["gold"]["priority"]
        exact += pred == gold
        under += LEVELS.index(pred) > LEVELS.index(gold)
        print(f"{c['case_id']} gold {gold} pred {pred} {'OK' if pred == gold else ('UNDER' if LEVELS.index(pred) > LEVELS.index(gold) else 'over')}")
    print(f"\npriority exact: {exact}/{len(sup)}   under-triaged: {under}")

    if args.seed:
        from app.main import CaseIn, create_case
        db.init()
        rng = random.Random(1)
        for c in sup:
            created = (datetime.now() - timedelta(minutes=rng.randint(1, 120))).isoformat(timespec="seconds")
            p = c["patient"]
            create_case(CaseIn(name=p["name"], age=p["age"], sex=p["sex"], language=c["language"],
                               text=" ".join(i["content"] for i in c["inputs"]), vitals=c.get("vitals") or {}), "seed", created)
        print(f"seeded {len(sup)} cases into {config.DB_PATH}")


if __name__ == "__main__":
    main()
