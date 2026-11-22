"""A-06: structural, provenance and reproducibility checks for A-03 to A-05.

These are *software/scientific-integrity checks*, NOT empirical proof of
curriculum coverage, job-market representativeness, or model accuracy.
No reference labels or ground-truth precision/recall/F1 are generated.

From the SkillDrift repository root (one-line command also works):

python -B -m validation.scientific_checks \\
  --curriculum data/processed/curriculum_topics.csv \\
  --aliases data/reference/skill_aliases.csv \\
  --snapshot outputs/skill_snapshot_2026-11-22.csv \\
  --output /tmp/skilldrift_a06_validation_v0.json

Never overwrites the output and never edits any project input data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from analysis.gap_analysis import SKILLS, build_audit, read_snapshot, write_audit
from evaluation.evaluate import check_provisional_inputs, make_review_template, TEMPLATE_COLUMNS
from nlp.match_curriculum import find_candidates, literal_phrase_present, write_candidates
from nlp.normalize_skills import load_aliases, lookup_key


SOURCE_FIELDS = ('source_url', 'source_locator', 'source_page', 'evidence_scope')


def _read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open('r', newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f'Missing CSV header: {path}')
        return list(reader.fieldnames), list(reader)


def _reversed_csv(original: str | Path, destination: Path) -> None:
    """Copy in reverse row order without touching the original input file."""
    columns, rows = _read_csv(original)
    with destination.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(reversed(rows))


def check_candidate_provenance(curriculum_path: str | Path,
                               aliases_path: str | Path,
                               candidates: list[dict[str, str]]) -> None:
    """Check that every A-03 candidate is traceable to its stated source field.

    This does NOT verify the underlying website or actual instruction.
    It only checks consistency with the selected source CSV.
    """
    _, curriculum_rows = _read_csv(curriculum_path)
    canonical_aliases = load_aliases(aliases_path)
    if set(info.canonical_skill for info in canonical_aliases.values()) != set(SKILLS):
        raise ValueError('Alias table canonical-skill set differs from the original 10 skills')

    primary: dict[tuple[str, str, str], dict[str, str]] = {}
    for topic in curriculum_rows:
        if topic.get('analysis_group') != 'PRIMARY_2025_2026':
            continue
        if topic.get('source_verification_status') == 'UNSUPPORTED':
            continue
        key = (topic.get('curriculum_id', ''), topic.get('course_id', ''), topic.get('topic_id', ''))
        if not all(key) or key in primary:
            raise ValueError('Incomplete or duplicate primary curriculum topic identifier')
        primary[key] = topic

    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        skill = candidate.get('canonical_skill', '')
        key = (candidate.get('curriculum_id', ''), candidate.get('course_id', ''), candidate.get('topic_id', ''))
        unique = (*key, skill)
        if unique in seen:
            raise ValueError('Duplicate A-03 candidate for a curriculum topic and skill')
        seen.add(unique)
        topic = primary.get(key)
        if topic is None:
            raise ValueError('A-03 candidate does not belong to selected supported primary curriculum')
        if skill not in SKILLS:
            raise ValueError(f'Unknown A-03 canonical skill: {skill!r}')
        phrase = candidate.get('matched_phrase', '')
        alias = canonical_aliases.get(lookup_key(phrase))
        if not phrase or alias is None or alias.canonical_skill != skill:
            raise ValueError(f'Matched phrase not in the alias table for {skill!r}')
        field = candidate.get('evidence_field', '')
        if field not in ('topic_text', 'skill_concept_candidate'):
            raise ValueError('Unsupported A-03 evidence field')
        if not literal_phrase_present(lookup_key(phrase), topic.get(field, '') or ''):
            raise ValueError(f'Matched phrase not present in declared source field for {key}')
        expected_method = 'exact' if lookup_key(phrase) == skill else 'alias'
        if candidate.get('match_method') != expected_method:
            raise ValueError('A-03 exact/alias match_method disagrees with alias table')
        for name in SOURCE_FIELDS:
            if candidate.get(name, '') != topic.get(name, ''):
                raise ValueError(f'A-03 source provenance mismatch for {name}')
        if not candidate.get('source_url') or not candidate.get('source_locator'):
            raise ValueError('Candidate missing source URL or locator')
        if (candidate.get('topic_text') != topic.get('topic_text')
                or candidate.get('source_verification_status') != topic.get('source_verification_status')
                or candidate.get('curriculum_review_status') != topic.get('review_status')
                or candidate.get('alias_reviewed_by') != alias.reviewed_by):
            raise ValueError('A-03 candidate source/review metadata mismatch')
        if candidate.get('coverage_status') != 'unknown' or candidate.get('coverage_score') != '':
            raise ValueError('Unapproved curriculum coverage detected')


def run_checks(curriculum: str | Path, aliases: str | Path,
               snapshot: str | Path) -> dict:
    """Recompute a disposable A-03/A-04/A-05 chain and verify its invariants."""
    curriculum, aliases, snapshot = (Path(p) for p in (curriculum, aliases, snapshot))
    candidates = find_candidates(curriculum, aliases)
    check_candidate_provenance(curriculum, aliases, candidates)
    snapshot_date, _ = read_snapshot(snapshot)

    with TemporaryDirectory(prefix='skilldrift-a06-') as temporary:
        root = Path(temporary)
        candidate_csv = root / 'candidates.csv'
        audit_csv = root / 'audit.csv'
        write_candidates(candidates, candidate_csv)
        audit_rows = build_audit(snapshot, candidate_csv)
        write_audit(audit_rows, audit_csv)
        check_provisional_inputs(audit_csv, candidate_csv)

        template = make_review_template(audit_csv, candidate_csv)
        if ([r.get('canonical_skill') for r in template] != list(SKILLS)
                or any(r.get(field) != '' for r in template
                       for field in TEMPLATE_COLUMNS if field != 'canonical_skill')):
            raise ValueError('A-05 reviewer template is not blank or omits a canonical skill')

        if (len(audit_rows) != len(SKILLS)
                or any(r['curriculum_coverage_status'] != 'unknown'
                       or r['curriculum_coverage_score'] != ''
                       or r['gap_assessment_status'] != 'NOT_ASSESSABLE'
                       or r['gap_score'] != '' for r in audit_rows)):
            raise ValueError('A-04 produces an unsupported coverage or gap assessment')

        # Metamorphic reproducibility: changing input row order should not
        # change the results. This is NOT a test of semantic correctness.
        reverse_curriculum = root / 'reversed_curriculum.csv'
        reverse_snapshot = root / 'reversed_snapshot.csv'
        _reversed_csv(curriculum, reverse_curriculum)
        _reversed_csv(snapshot, reverse_snapshot)
        reversed_candidates = find_candidates(reverse_curriculum, aliases)
        check_candidate_provenance(reverse_curriculum, aliases, reversed_candidates)
        if candidates != reversed_candidates:
            raise ValueError('A-03 candidates changed with curriculum row order')
        reversed_audit = build_audit(reverse_snapshot, candidate_csv)
        if audit_rows != reversed_audit:
            raise ValueError('A-04 audit changed with industry snapshot row order')

        # Re-running the same pipeline produces identical serialized files.
        candidate_replay = root / 'candidates_replay.csv'
        audit_replay = root / 'audit_replay.csv'
        write_candidates(reversed_candidates, candidate_replay)
        write_audit(reversed_audit, audit_replay)
        if (candidate_csv.read_bytes() != candidate_replay.read_bytes()
                or audit_csv.read_bytes() != audit_replay.read_bytes()):
            raise ValueError('A-03/A-04 CSV serialization is not reproducible')

        report = {
            'validation_status': 'PROVISIONAL_PIPELINE_CHECKS_PASSED',
            'validation_scope': 'Structural checks, in-CSV provenance and row-order reproducibility; no independently reviewed gold labels',
            'snapshot_date': snapshot_date,
            'canonical_skill_count': len(SKILLS),
            'literal_candidate_count': len(candidates),
            'candidate_topic_text_count': sum(c['evidence_field'] == 'topic_text' for c in candidates),
            'candidate_researcher_concept_count': sum(c['evidence_field'] == 'skill_concept_candidate' for c in candidates),
            'audit_row_count': len(audit_rows),
            'checks': {
                'source_csv_provenance_consistent': True,
                'primary_only_and_excludes_unsupported': True,
                'candidate_fields_traceable': True,
                'a03_a04_counts_and_source_links_consistent': True,
                'curriculum_row_order_invariant': True,
                'snapshot_row_order_invariant': True,
                'serialized_output_deterministic': True,
                'all_curriculum_coverage_unknown': True,
                'all_gap_scores_blank': True,
                'human_review_template_blinded': True,
            },
            'sha256_of_inputs': {
                'curriculum': hashlib.sha256(curriculum.read_bytes()).hexdigest(),
                'aliases': hashlib.sha256(aliases.read_bytes()).hexdigest(),
                'snapshot': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            },
            'sha256_of_recomputed_outputs': {
                'a03_candidates': hashlib.sha256(candidate_csv.read_bytes()).hexdigest(),
                'a04_audit': hashlib.sha256(audit_csv.read_bytes()).hexdigest(),
            },
            'real_evaluation_metrics_available': False,
            'limitations': [
                'This report validates local CSV consistency and deterministic processing, not the truth of external websites.',
                'Curriculum coverage, actual classroom teaching and missing skills remain unverified.',
                'Precision/recall/F1 require independent human labels for all ten skills.',
                'The industry snapshot describes observed job listings, not the population of jobs.',
                'This is not approval of proposed shared output contracts or matching methodology.',
            ],
        }
    return report


def write_report(report: dict, output: str | Path,
                 input_paths: tuple[str | Path, ...] = ()) -> None:
    path = Path(output)
    if path.resolve() in {Path(p).resolve() for p in input_paths}:
        raise ValueError('Output must differ from all inputs')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--curriculum', type=Path, required=True)
    parser.add_argument('--aliases', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        inputs = (args.curriculum, args.aliases, args.snapshot)
        if args.output.resolve() in {p.resolve() for p in inputs}:
            raise ValueError('Output must differ from all inputs')
        report = run_checks(*inputs)
        write_report(report, args.output, inputs)
    except (ValueError, OSError) as error:
        print(f'A-06 validation error: {error}', file=sys.stderr)
        return 1
    print(f'A-06 provisional checks passed for {report["canonical_skill_count"]} skills; '
          f'{report["literal_candidate_count"]} literal candidates.')
    print(f'Wrote reproducibility/provenance report to {args.output}. NO ground-truth metrics or coverage scores.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
