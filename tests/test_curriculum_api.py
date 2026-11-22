"""P-04 API integration tests: honest research status and no source mutations."""

import csv
from fastapi.testclient import TestClient
from backend import main
from analysis.gap_analysis import SKILLS
from nlp.match_curriculum import COLUMNS as A03_COLUMNS, REQUIRED as CURRICULUM_COLUMNS


def _write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)


def _setup(tmp_path, monkeypatch):
    curriculum = tmp_path / "data" / "processed" / "curriculum_topics.csv"
    aliases = tmp_path / "data" / "reference" / "skill_aliases.csv"
    snapshot = tmp_path / "outputs" / "skill_snapshot_2026-11-22.csv"
    primary = dict.fromkeys(CURRICULUM_COLUMNS, "")
    primary.update({
        "curriculum_id": "c1", "course_id": "CS632", "topic_id": "topic-1",
        "topic_text": "SQL database topics", "analysis_group": "PRIMARY_2025_2026",
        "source_verification_status": "VERIFIED", "review_status": "PENDING",
        "source_url": "https://example.edu/course", "source_locator": "reading list",
        "evidence_scope": "reading_list",
    })
    historical = dict(primary, curriculum_id="c2", course_id="CS317",
                      topic_id="topic-2", analysis_group="HISTORICAL_2008")
    unsupported = dict(primary, curriculum_id="c3", course_id="CS631",
                       topic_id="topic-3", source_verification_status="UNSUPPORTED")
    _write_csv(curriculum, CURRICULUM_COLUMNS, [primary, historical, unsupported])
    aliases.parent.mkdir(parents=True, exist_ok=True)
    aliases.write_text("placeholder\n", encoding="utf-8")
    _write_csv(snapshot, ("Date", "Skill", "Mumbai %", "Pune %", "Bengaluru %"), [
        {"Date": "2026-11-22", "Skill": skill, "Mumbai %": "20", "Pune %": "30", "Bengaluru %": "40"}
        for skill in SKILLS
    ])
    monkeypatch.setattr(main, "CURRICULUM_PATH", curriculum)
    monkeypatch.setattr(main, "ALIASES_PATH", aliases)
    monkeypatch.setattr(main, "OUTPUTS_DIR", snapshot.parent)
    return curriculum, aliases, snapshot


def _fake_candidates():
    candidate = dict.fromkeys(A03_COLUMNS, "")
    candidate.update({
        "curriculum_id": "c1", "canonical_skill": "sql", "course_id": "CS632",
        "topic_id": "topic-1", "topic_text": "SQL database topics",
        "matched_phrase": "sql", "evidence_field": "topic_text", "match_method": "exact",
        "source_verification_status": "VERIFIED", "curriculum_review_status": "PENDING",
        "source_url": "https://example.edu/course", "source_locator": "reading list",
        "evidence_scope": "reading_list", "coverage_status": "unknown", "coverage_score": "",
    })
    return [candidate]


def test_curriculum_excludes_historical_and_unsupported(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    response = TestClient(main.app).get("/api/curriculum")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["rows"][0]["course_id"] == "CS632"
    assert body["curriculum_coverage_status"] == "unknown"
    assert body["historical_cs317_excluded"] is True


def test_gap_endpoint_preserves_unknown_and_does_not_write_outputs(tmp_path, monkeypatch):
    curriculum, aliases, snapshot = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(main, "_candidate_rows", _fake_candidates)
    before = {p: p.read_bytes() for p in (curriculum, aliases, snapshot)}
    response = TestClient(main.app).get("/api/skill-gaps")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["count"] == 10
    assert body["literal_candidate_count"] == 1
    assert body["analysis_status"] == "PROVISIONAL_EVIDENCE_ONLY"
    assert all(row["curriculum_coverage_status"] == "unknown" for row in body["rows"])
    assert all(row["gap_assessment_status"] == "NOT_ASSESSABLE" for row in body["rows"])
    assert all(row["gap_score"] == "" for row in body["rows"])
    assert next(row for row in body["rows"] if row["canonical_skill"] == "sql")["literal_candidate_count"] == "1"
    assert next(row for row in body["rows"] if row["canonical_skill"] == "sql")["Mumbai %"] == 20.0
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert sorted(p.name for p in snapshot.parent.iterdir()) == [snapshot.name]


def test_evaluation_does_not_invent_metrics(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(main, "_candidate_rows", _fake_candidates)
    response = TestClient(main.app).get("/api/evaluation")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["metrics"] is None
    assert body["reference_labels_complete"] is False
    assert body["sample_size_skills"] == 10
    assert body["gap_assessment_status"] == "NOT_ASSESSABLE"


def test_missing_alias_input_returns_503(tmp_path, monkeypatch):
    _, aliases, _ = _setup(tmp_path, monkeypatch)
    aliases.unlink()
    response = TestClient(main.app).get("/api/skill-gaps")
    assert response.status_code == 503
    assert "skill_aliases.csv" in response.json()["detail"]
