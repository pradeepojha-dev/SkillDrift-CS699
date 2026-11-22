"""SkillDrift prototype: read-only API for the existing job-market results.

Run from repository root:
    python -m uvicorn backend.main:app --reload

Existing October and November data are not recalculated or changed.
This is a provisional Pradeep-owned API; shared interfaces require team agreement.
"""

import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SNAPSHOT_COLUMNS = {"Date", "Skill", "Mumbai %", "Pune %", "Bengaluru %"}

app = FastAPI(title="SkillDrift API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def load_csv(path: Path, required: set[str]) -> list[dict]:
    if not path.is_file():
        raise HTTPException(status_code=503, detail=f"Required output missing: {path.name}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns = set(reader.fieldnames or [])
            missing = required - columns
            if missing:
                raise HTTPException(
                    status_code=503,
                    detail=f"Invalid {path.name}: missing columns {sorted(missing)}",
                )
            rows = []
            for row in reader:
                parsed = {}
                for name, raw in row.items():
                    value = raw.strip() if isinstance(raw, str) else raw
                    if name.endswith(" %") or name.endswith(" Change") or name.endswith(" %_Old") or name.endswith(" %_New"):
                        if value not in (None, ""):
                            try:
                                value = float(value)
                            except ValueError as exc:
                                raise ValueError(f"Non-numeric {name} in {path.name}") from exc
                    parsed[name] = value
                rows.append(parsed)
            return rows
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Cannot read {path.name}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok", "project": "SkillDrift"}


@app.get("/api/snapshots")
def snapshots():
    paths = sorted(OUTPUTS_DIR.glob("skill_snapshot_????-??-??.csv"))
    if not paths:
        raise HTTPException(status_code=503, detail="No dated skill snapshots found")
    result = []
    for path in paths:
        result.append({"date": path.stem.removeprefix("skill_snapshot_"),
                       "rows": load_csv(path, SNAPSHOT_COLUMNS)})
    return {"count": len(result), "snapshots": result,
            "note": "Percentages describe observed job samples, not industry-wide demand."}


@app.get("/api/skill-drift")
def skill_drift():
    rows = load_csv(OUTPUTS_DIR / "skill_drift_latest.csv", {"Skill"})
    return {"count": len(rows), "rows": rows,
            "note": "Changes are in percentage points for observed job samples; 5 pp trend cutoff is a prototype rule."}
