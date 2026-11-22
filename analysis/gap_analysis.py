"""A-04 provisional SkillDrift demand–curriculum evidence audit (NOT a gap score).

Reads one dated 10-skill job-sample snapshot and the A-03 provisional literal
candidate CSV. Produces one row per canonical industry skill. Unreviewed
curriculum evidence cannot establish coverage; absence of a literal candidate
cannot establish a curriculum gap. All coverage and gap scores remain blank.

Run from the SkillDrift repository root, after generating the A-03 CSV:

  python -B -m analysis.gap_analysis \\
      --snapshot outputs/skill_snapshot_2026-11-22.csv \\
      --candidates /tmp/skilldrift_a03_candidates_v0.csv \\
      --output /tmp/skilldrift_a04_gap_audit_v0.csv

This CSV is an independent provisional research artifact; it is not an approved
shared contract or an input to Pradeep's backend until the team agrees.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
import sys

SKILLS = (
    'python', 'sql', 'pyspark', 'snowflake', 'aws', 'airflow',
    'azure data factory', 'gcp', 'etl', 'data pipelines',
)
CITY_COLUMNS = ('Mumbai %', 'Pune %', 'Bengaluru %')
SNAPSHOT_COLUMNS = ('Date', 'Skill', *CITY_COLUMNS)
CANDIDATE_COLUMNS = (
    'curriculum_id', 'canonical_skill', 'course_id', 'topic_id',
    'evidence_field', 'source_url', 'source_locator', 'evidence_scope',
    'coverage_status', 'coverage_score', 'curriculum_review_status',
    'alias_reviewed_by',
)
OUTPUT_COLUMNS = (
    'snapshot_date', 'canonical_skill', *CITY_COLUMNS,
    'literal_candidate_count', 'topic_text_candidate_count',
    'researcher_concept_candidate_count', 'candidate_course_ids',
    'candidate_topic_ids', 'candidate_evidence_scopes', 'candidate_source_urls',
    'candidate_review_statuses', 'candidate_alias_review_statuses',
    'demand_scope', 'evidence_status', 'curriculum_coverage_status', 'curriculum_coverage_score',
    'gap_assessment_status', 'gap_score', 'human_review_required',
    'interpretation',
)


def _csv_reader(path: str | Path, required: tuple[str, ...]):
    """Return rows with required columns checked; rows are not modified."""
    with Path(path).open('r', newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(col not in reader.fieldnames for col in required):
            raise ValueError(f'{path}: missing required columns: '
                             f'{[col for col in required if col not in (reader.fieldnames or [])]}')
        return list(reader)


def read_snapshot(path: str | Path) -> tuple[str, dict[str, dict[str, str]]]:
    rows = _csv_reader(path, SNAPSHOT_COLUMNS)
    indexed: dict[str, dict[str, str]] = {}
    dates: set[str] = set()
    for row in rows:
        skill = (row['Skill'] or '').strip()
        if skill not in SKILLS:
            raise ValueError(f'{path}: unexpected canonical skill {skill!r}')
        if skill in indexed:
            raise ValueError(f'{path}: duplicate skill {skill!r}')
        day = (row['Date'] or '').strip()
        try:
            if date.fromisoformat(day).isoformat() != day:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f'{path}: invalid ISO snapshot date {day!r}') from exc
        dates.add(day)
        for column in CITY_COLUMNS:
            raw = (row[column] or '').strip()
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f'{path}: invalid percentage for {skill}: {column}={raw!r}') from exc
            if not (0 <= value <= 100):
                raise ValueError(f'{path}: out-of-range percentage for {skill}: {column}={raw!r}')
        indexed[skill] = row
    if len(dates) != 1:
        raise ValueError(f'{path}: expected one dated snapshot, got {sorted(dates)}')
    if set(indexed) != set(SKILLS):
        raise ValueError(f'{path}: expected all 10 canonical skills; missing {sorted(set(SKILLS) - set(indexed))}')
    return next(iter(dates)), indexed


def read_candidates(path: str | Path) -> dict[str, list[dict[str, str]]]:
    rows = _csv_reader(path, CANDIDATE_COLUMNS)
    grouped: dict[str, list[dict[str, str]]] = {skill: [] for skill in SKILLS}
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        skill = (row['canonical_skill'] or '').strip()
        course = (row['course_id'] or '').strip()
        topic = (row['topic_id'] or '').strip()
        if skill not in SKILLS or not course or not topic:
            raise ValueError(f'{path}: unexpected or incomplete skill/course/topic')
        if course == 'CS317':
            raise ValueError(f'{path}: historical CS317 cannot enter primary A-04 analysis')
        key = (skill, course, topic)
        if key in seen:
            raise ValueError(f'{path}: duplicate candidate {key!r}')
        seen.add(key)
        if (row['evidence_field'] or '').strip() not in {'topic_text', 'skill_concept_candidate'}:
            raise ValueError(f'{path}: unexpected candidate evidence field for {key!r}')
        if ((row['coverage_status'] or '').strip().lower() != 'unknown'
                or (row['coverage_score'] or '').strip()):
            raise ValueError(f'{path}: A-04 only accepts provisional UNKNOWN/blank coverage for {key!r}')
        # An A-03 literal mention never constitutes verified instructional coverage,
        # even if source metadata describes the web page as VERIFIED.
        grouped[skill].append(row)
    return grouped


def build_audit(snapshot: str | Path, candidates: str | Path) -> list[dict[str, str]]:
    snapshot_date, demand = read_snapshot(snapshot)
    evidence = read_candidates(candidates)
    output: list[dict[str, str]] = []
    for skill in SKILLS:
        matches = evidence[skill]
        text_hits = sum(r['evidence_field'] == 'topic_text' for r in matches)
        concept_hits = sum(r['evidence_field'] == 'skill_concept_candidate' for r in matches)
        status = 'LITERAL_CANDIDATES_UNREVIEWED' if matches else 'NO_LITERAL_CANDIDATE'
        interpretation = (
            'Literal curriculum mention candidates exist, but source/alias review and '
            'instructional coverage validation are pending; this is not a proven skill gap.'
            if matches else
            'No literal candidates detected by A-03. This does not establish that the '
            'skill is absent from the curriculum or that a skill gap exists.'
        )
        row = {
            'snapshot_date': snapshot_date,
            'canonical_skill': skill,
            **{col: (demand[skill][col] or '').strip() for col in CITY_COLUMNS},
            'literal_candidate_count': str(len(matches)),
            'topic_text_candidate_count': str(text_hits),
            'researcher_concept_candidate_count': str(concept_hits),
            'candidate_course_ids': ';'.join(sorted({r['course_id'] for r in matches})),
            'candidate_topic_ids': ';'.join(sorted({r['topic_id'] for r in matches})),
            'candidate_evidence_scopes': ';'.join(sorted({(r['evidence_scope'] or '').strip() for r in matches if r['evidence_scope']})),
            'candidate_source_urls': ';'.join(sorted({(r['source_url'] or '').strip() for r in matches if r['source_url']})),
            'candidate_review_statuses': ';'.join(sorted({(r['curriculum_review_status'] or '').strip() for r in matches if r['curriculum_review_status']})),
            'candidate_alias_review_statuses': ';'.join(sorted({(r['alias_reviewed_by'] or '').strip() for r in matches if r['alias_reviewed_by']})),
            'demand_scope': 'observed_job_listing_samples_only',
            'evidence_status': status,
            'curriculum_coverage_status': 'unknown',
            'curriculum_coverage_score': '',
            'gap_assessment_status': 'NOT_ASSESSABLE',
            'gap_score': '',
            'human_review_required': 'true',
            'interpretation': interpretation,
        }
        output.append(row)
    return output


def write_audit(rows: list[dict[str, str]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--candidates', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.resolve() in {args.snapshot.resolve(), args.candidates.resolve()}:
        parser.error('Output must differ from both inputs')
    try:
        rows = build_audit(args.snapshot, args.candidates)
        write_audit(rows, args.output)
    except (OSError, ValueError) as exc:
        print(f'A-04 audit error: {exc}', file=sys.stderr)
        return 1
    print(f'Wrote {len(rows)} provisional 10-skill audit rows to {args.output}')
    print('Coverage UNKNOWN; gaps NOT_ASSESSABLE; no gap scores produced.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
