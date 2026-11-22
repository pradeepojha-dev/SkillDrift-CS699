"""SkillDrift CS699 research prototype: read-only job and curriculum API.

The new curriculum endpoints integrate A-03/A-04/A-05 without modifying those
algorithms or generating/replacing any repository data files. Results are
provisional and do not establish what is taught or which skills are missing.

Run from repository root: python -m uvicorn backend.main:app --reload
"""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CURRICULUM_PATH = PROJECT_ROOT / "data" / "processed" / "curriculum_topics.csv"
ALIASES_PATH = PROJECT_ROOT / "data" / "reference" / "skill_aliases.csv"
SNAPSHOT_COLUMNS = {"Date", "Skill", "Mumbai %", "Pune %", "Bengaluru %"}

app = FastAPI(title="SkillDrift API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def load_csv(path: Path, required: set[str]) -> list[dict]:
    """Load a source CSV without changing it; preserve existing API behavior."""
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
                    if (name.endswith(" %") or name.endswith(" Change")
                            or name.endswith(" %_Old") or name.endswith(" %_New")):
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
        result.append({
            "date": path.stem.removeprefix("skill_snapshot_"),
            "rows": load_csv(path, SNAPSHOT_COLUMNS),
        })
    return {
        "count": len(result), "snapshots": result,
        "note": "Percentages describe observed job samples, not industry-wide demand.",
    }


@app.get("/api/skill-drift")
def skill_drift():
    rows = load_csv(OUTPUTS_DIR / "skill_drift_latest.csv", {"Skill"})
    return {
        "count": len(rows), "rows": rows,
        "note": "Changes are in percentage points for observed job samples; 5 pp trend cutoff is a prototype rule.",
    }


@app.get("/api/curriculum")
def curriculum():
    """Selected 2025-26 research topics only; historical CS317 is excluded."""
    # Follow the already implemented A-03 input schema (do not invent columns).
    from nlp.match_curriculum import REQUIRED as REQUIRED_CURRICULUM_COLUMNS

    rows = load_csv(CURRICULUM_PATH, set(REQUIRED_CURRICULUM_COLUMNS))
    selected = [
        row for row in rows
        if row["analysis_group"] == "PRIMARY_2025_2026"
        and row["source_verification_status"] != "UNSUPPORTED"
    ]
    if not selected:
        raise HTTPException(status_code=503, detail="No selected primary curriculum topics found")
    return {
        "count": len(selected),
        "rows": selected,
        "scope": "Selected IIT Bombay CSE research topics (2025-2026), not the full curriculum",
        "historical_cs317_excluded": True,
        "curriculum_coverage_status": "unknown",
        "note": "These are research records requiring human source review, not confirmed taught skills.",
    }


def _candidate_rows() -> list[dict[str, str]]:
    """Call Abhay's existing A-03 implementation without altering it."""
    from nlp.match_curriculum import find_candidates
    return find_candidates(CURRICULUM_PATH, ALIASES_PATH)


def _provisional_analysis(with_review_template: bool = False):
    """Run existing A-03/A-04 (and optional A-05) using temporary outputs.

    No output CSVs are saved inside the repository or overwritten.
    """
    from analysis.gap_analysis import SKILLS, build_audit, write_audit
    from nlp.match_curriculum import write_candidates

    snapshot_path = OUTPUTS_DIR / "skill_snapshot_2026-11-22.csv"
    for path in (CURRICULUM_PATH, ALIASES_PATH, snapshot_path):
        if not path.is_file():
            raise HTTPException(status_code=503, detail=f"Required research input missing: {path.name}")
    try:
        candidates = _candidate_rows()
        with TemporaryDirectory(prefix="skilldrift_api_") as directory:
            scratch = Path(directory)
            candidates_path = scratch / "a03_candidates.csv"
            write_candidates(candidates, candidates_path)
            audit = build_audit(snapshot_path, candidates_path)
            if len(audit) != len(SKILLS):
                raise ValueError("A-04 did not produce 10 canonical skill rows")
            for row in audit:
                if (row["curriculum_coverage_status"] != "unknown"
                        or row["curriculum_coverage_score"] != ""
                        or row["gap_assessment_status"] != "NOT_ASSESSABLE"
                        or row["gap_score"] != ""):
                    raise ValueError("Unreviewed analysis unexpectedly claims curriculum coverage or a gap score")
                # Match the existing snapshot endpoint's numeric percentages.
                for city_column in ("Mumbai %", "Pune %", "Bengaluru %"):
                    row[city_column] = float(row[city_column])
            if with_review_template:
                from evaluation.evaluate import make_review_template
                audit_path = scratch / "a04_audit.csv"
                # A-05 expects a CSV, not in-memory data. Restore CSV strings.
                for row in audit:
                    for column in ("Mumbai %", "Pune %", "Bengaluru %"):
                        row[column] = str(row[column])
                write_audit(audit, audit_path)
                template = make_review_template(audit_path, candidates_path)
                return audit, candidates, template
            return audit, candidates, None
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=503, detail=f"Provisional curriculum analysis failed: {exc}") from exc


@app.get("/api/skill-gaps")
def skill_gaps():
    """Expose evidence audit only; do not imply validated educational gaps."""
    rows, candidates, _ = _provisional_analysis()
    return {
        "count": len(rows), "rows": rows,
        "literal_candidate_count": len(candidates),
        "analysis_status": "PROVISIONAL_EVIDENCE_ONLY",
        "note": ("All curriculum coverage is UNKNOWN and all gaps are NOT_ASSESSABLE. "
                 "Industry percentages reflect observed job samples only."),
    }


@app.get("/api/evaluation")
def evaluation_status():
    """Report evaluation availability; never generate fictitious metrics."""
    rows, candidates, blank_template = _provisional_analysis(with_review_template=True)
    return {
        "evaluation_status": "HUMAN_REFERENCE_LABELS_NOT_CONFIGURED",
        "reference_labels_complete": False,
        "benchmark": "Ten-skill literal-mention detection, not curriculum coverage",
        "sample_size_skills": len(blank_template),
        "literal_candidate_count": len(candidates),
        "metrics": None,
        "note": ("A-05 generated a blank human-review template. Precision, recall and F1 "
                 "cannot be reported without independently reviewed complete labels."),
        "curriculum_coverage_status": "unknown",
        "gap_assessment_status": "NOT_ASSESSABLE",
    }
