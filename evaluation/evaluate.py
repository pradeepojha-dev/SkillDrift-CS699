"""A-05: human-labeled *literal-mention detection* evaluation, not coverage.

Two-step workflow from the repository root:
  python -B -m evaluation.evaluate prepare \\
      --audit /tmp/skilldrift_a04_gap_audit_v0.csv \\
      --candidates /tmp/skilldrift_a03_candidates_v0.csv \\
      --output /tmp/skilldrift_a05_manual_labels_v0.csv

A human independently reviews all ten canonical skills against the entire
selected primary curriculum corpus (including topic_text and labeled derived
skill_concept_candidate fields), fills reference_label, reviewer, review_date
and manual_evidence, and only then runs:

  python -B -m evaluation.evaluate score \\
      --audit /tmp/skilldrift_a04_gap_audit_v0.csv \\
      --candidates /tmp/skilldrift_a03_candidates_v0.csv \\
      --labels /tmp/skilldrift_a05_manual_labels_v0.csv \\
      --output /tmp/skilldrift_a05_eval_report_v0.json

The ten-skill benchmark tests whether A-03 detects at least one relevant
literal mention for a skill in the selected corpus; NOT whether a skill was
actually taught, mastered, or is absent. No metrics without complete independent
human reference labels. Outputs never overwrite an existing file.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
import sys

from analysis.gap_analysis import SKILLS, CITY_COLUMNS, read_candidates

TEMPLATE_COLUMNS = (
    'canonical_skill', 'reference_label', 'reviewer', 'review_date',
    'manual_evidence', 'review_notes',
)
AUDIT_REQUIRED = (
    'snapshot_date', 'canonical_skill', *CITY_COLUMNS,
    'literal_candidate_count', 'topic_text_candidate_count',
    'researcher_concept_candidate_count', 'candidate_course_ids',
    'candidate_topic_ids', 'candidate_evidence_scopes', 'candidate_source_urls',
    'evidence_status', 'curriculum_coverage_status', 'curriculum_coverage_score',
    'gap_assessment_status', 'gap_score', 'human_review_required',
    'demand_scope',
)


def _read_csv(path: str | Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with Path(path).open('r', newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(x not in reader.fieldnames for x in required):
            raise ValueError(f'{path}: missing required fields')
        return list(reader)


def _file_is_distinct(output: Path, inputs: list[Path]) -> None:
    if output.resolve() in {p.resolve() for p in inputs}:
        raise ValueError('Output must differ from all input files')


def _safe_int(value: str | None, label: str) -> int:
    try:
        if value is None or str(int(value)) != value.strip() or int(value) < 0:
            raise ValueError
        return int(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'Invalid nonnegative integer for {label}: {value!r}') from exc


def check_provisional_inputs(audit_path: str | Path, candidates_path: str | Path) -> dict[str, dict[str, str]]:
    """Check A-04/A-03 provenance and counts before any human evaluation."""
    audit = _read_csv(audit_path, AUDIT_REQUIRED)
    evidence = read_candidates(candidates_path)
    if len(audit) != len(SKILLS):
        raise ValueError(f'Expected exactly {len(SKILLS)} A-04 skill rows')
    indexed: dict[str, dict[str, str]] = {}
    dates: set[str] = set()
    for row in audit:
        skill = (row['canonical_skill'] or '').strip()
        if skill not in SKILLS or skill in indexed:
            raise ValueError(f'Unexpected or duplicated A-04 skill: {skill!r}')
        day = (row['snapshot_date'] or '').strip()
        try:
            if day != date.fromisoformat(day).isoformat():
                raise ValueError
        except ValueError as exc:
            raise ValueError(f'Invalid snapshot date: {day!r}') from exc
        dates.add(day)
        for col in CITY_COLUMNS:
            try:
                percentage = float(row[col])
            except (ValueError, TypeError) as exc:
                raise ValueError(f'Invalid demand percentage for {skill}/{col}') from exc
            if not 0 <= percentage <= 100:
                raise ValueError(f'Out-of-range demand percentage for {skill}/{col}')
        checks = {
            'literal_candidate_count': len(evidence[skill]),
            'topic_text_candidate_count': sum(r['evidence_field'] == 'topic_text' for r in evidence[skill]),
            'researcher_concept_candidate_count': sum(r['evidence_field'] == 'skill_concept_candidate' for r in evidence[skill]),
        }
        for field, expected in checks.items():
            if _safe_int(row[field], f'{skill}/{field}') != expected:
                raise ValueError(f'A-03/A-04 count mismatch for {skill}/{field}')
        expected_status = 'LITERAL_CANDIDATES_UNREVIEWED' if evidence[skill] else 'NO_LITERAL_CANDIDATE'
        if (row['evidence_status'] != expected_status
                or row['candidate_course_ids'] != ';'.join(sorted({r['course_id'] for r in evidence[skill]}))
                or row['candidate_topic_ids'] != ';'.join(sorted({r['topic_id'] for r in evidence[skill]}))
                or row['candidate_evidence_scopes'] != ';'.join(sorted({r['evidence_scope'].strip() for r in evidence[skill] if r['evidence_scope']}))
                or row['candidate_source_urls'] != ';'.join(sorted({r['source_url'].strip() for r in evidence[skill] if r['source_url']}))):
            raise ValueError(f'A-03/A-04 provenance or status mismatch for {skill}')
        if (row['curriculum_coverage_status'] != 'unknown' or row['curriculum_coverage_score'].strip()
                or row['gap_assessment_status'] != 'NOT_ASSESSABLE' or row['gap_score'].strip()
                or row['human_review_required'] != 'true'
                or row['demand_scope'] != 'observed_job_listing_samples_only'):
            raise ValueError(f'Unexpected coverage, gap score, or demand-scope claim for {skill}')
        indexed[skill] = row
    if set(indexed) != set(SKILLS) or len(dates) != 1:
        raise ValueError('Expected all ten canonical skills from one snapshot date')
    return indexed


def make_review_template(audit_path: str | Path, candidates_path: str | Path) -> list[dict[str, str]]:
    """Return a blinded template: no predictions, suggested labels or scores."""
    check_provisional_inputs(audit_path, candidates_path)
    return [dict.fromkeys(TEMPLATE_COLUMNS, '') | {'canonical_skill': skill} for skill in SKILLS]


def _read_reviewed_labels(path: str | Path) -> dict[str, bool]:
    rows = _read_csv(path, TEMPLATE_COLUMNS)
    if len(rows) != len(SKILLS):
        raise ValueError('All ten skills must be independently labeled before evaluation')
    labels = {}
    for row in rows:
        skill = (row['canonical_skill'] or '').strip()
        if skill not in SKILLS or skill in labels:
            raise ValueError(f'Unknown or duplicate reviewed skill: {skill!r}')
        label = (row['reference_label'] or '').strip().lower()
        if label not in {'present', 'absent'}:
            raise ValueError(f'Incomplete/invalid human reference label for {skill}: use present or absent')
        reviewer = (row['reviewer'] or '').strip()
        reviewed_on = (row['review_date'] or '').strip()
        reference = (row['manual_evidence'] or '').strip()
        if not reviewer or not reviewed_on or not reference:
            raise ValueError(f'Missing reviewer, review_date, or independent manual_evidence for {skill}')
        try:
            if date.fromisoformat(reviewed_on).isoformat() != reviewed_on:
                raise ValueError
        except ValueError as exc:
            raise ValueError(f'Invalid ISO review_date for {skill}') from exc
        labels[skill] = (label == 'present')
    if set(labels) != set(SKILLS):
        raise ValueError('Human labels must cover all ten canonical skills')
    return labels


def evaluate_reviewed(audit_path: str | Path, candidates_path: str | Path,
                      labels_path: str | Path) -> dict:
    """Score at *skill* level only after full independent manual labeling."""
    audit = check_provisional_inputs(audit_path, candidates_path)
    labels = _read_reviewed_labels(labels_path)
    tp = fp = tn = fn = 0
    disagreements = []
    for skill in SKILLS:
        predicted = _safe_int(audit[skill]['literal_candidate_count'], skill) > 0
        reference = labels[skill]
        if predicted and reference:
            tp += 1
        elif predicted and not reference:
            fp += 1
        elif not predicted and reference:
            fn += 1
        else:
            tn += 1
        if predicted != reference:
            disagreements.append({'canonical_skill': skill,
                                  'prediction': 'present' if predicted else 'absent',
                                  'reference': 'present' if reference else 'absent',
                                  'error_type': 'FP' if predicted else 'FN'})
    def ratio(top, bottom):
        return round(top / bottom, 4) if bottom else None
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    f1 = (round(2 * tp / (2 * tp + fp + fn), 4) if (2 * tp + fp + fn) else None)
    return {
        'evaluation_status': 'HUMAN_REFERENCE_LABELS_COMPLETE',
        'benchmark_definition': 'Presence of >=1 relevant literal mention per skill in the selected primary curriculum topic_text or researcher-assigned skill_concept_candidate corpus',
        'unit_of_analysis': 'canonical_skill (10 skills; not candidate rows or all course-skill pairs)',
        'snapshot_date': next(iter(audit.values()))['snapshot_date'],
        'sample_size_skills': len(SKILLS),
        'confusion_matrix': {'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn},
        'metrics': {'precision': precision, 'recall': recall, 'f1': f1,
                    'accuracy': ratio(tp + tn, len(SKILLS))},
        'disagreements': disagreements,
        'limitations': [
            'Measures skill-level literal mention detection only, NOT taught curriculum coverage or skill gaps.',
            'Reference labels must be independently reviewed across the entire selected primary corpus.',
            'Ten selected skills form a small nonrandom benchmark; results are not generalizable.',
            'Skill-level evaluation cannot measure individual candidate false-positive rates.',
            'A-04 demand values reflect observed job-listing samples, not the population.',
            'All actual curriculum coverage and gap scores remain unknown/not assessable.',
        ],
    }


def write_review_template(rows: list[dict[str, str]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=TEMPLATE_COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def write_json(report: dict, output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_subparsers(dest='mode', required=True)
    for name in ('prepare', 'score'):
        child = mode.add_parser(name)
        child.add_argument('--audit', type=Path, required=True)
        child.add_argument('--candidates', type=Path, required=True)
        if name == 'score':
            child.add_argument('--labels', type=Path, required=True)
        child.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        inputs = [args.audit, args.candidates] + ([args.labels] if args.mode == 'score' else [])
        _file_is_distinct(args.output, inputs)
        if args.mode == 'prepare':
            rows = make_review_template(args.audit, args.candidates)
            write_review_template(rows, args.output)
            print(f'Wrote {len(rows)} BLANK human-label rows to {args.output}; NO metrics are available.')
            print('Independent review of all primary curriculum topics is required before scoring.')
        else:
            report = evaluate_reviewed(args.audit, args.candidates, args.labels)
            write_json(report, args.output)
            print(f'Wrote human-reviewed 10-skill literal-mention benchmark to {args.output}')
            print('Metrics do NOT measure course coverage, skills mastered, or curriculum gaps.')
    except (OSError, ValueError) as exc:
        print(f'A-05 evaluation error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
