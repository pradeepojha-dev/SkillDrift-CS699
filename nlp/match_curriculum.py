"""A-03 provisional literal curriculum-to-industry skill screening (NOT coverage scoring).

Read the selected primary curriculum topics and A-02's provisional skill aliases.
Emit only literal mention *candidates*, tagged by evidence origin (topic_text or
researcher-assigned skill_concept_candidate). Never infer 'covered' or 'missing'.

From repository root:
    python3 -B -m nlp.match_curriculum \
        --curriculum data/processed/curriculum_topics.csv \
        --aliases data/reference/skill_aliases.csv \
        --output /tmp/skilldrift_a03_candidates_v0.csv

Output is a new, explicitly PROVISIONAL audit; not the pending C-05 contract.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from nlp.normalize_skills import load_aliases

COLUMNS = (
    'curriculum_id', 'canonical_skill', 'course_id', 'topic_id',
    'topic_text', 'matched_phrase', 'evidence_field', 'match_method',
    'source_verification_status', 'curriculum_review_status',
    'alias_reviewed_by', 'source_url', 'source_locator', 'source_page',
    'evidence_scope', 'coverage_status', 'coverage_score', 'interpretation',
)
REQUIRED = (
    'curriculum_id', 'course_id', 'topic_id', 'topic_text',
    'skill_concept_candidate', 'source_verification_status',
    'review_status', 'analysis_group', 'source_url', 'source_locator',
    'source_page', 'evidence_scope',
)


def literal_phrase_present(phrase: str, text: str) -> bool:
    """Case-insensitive whole-phrase match; not fuzzy or semantic similarity."""
    normalized = unicodedata.normalize('NFKC', text).casefold()
    escaped = re.escape(phrase)
    return bool(re.search(r'(?<!\w)' + escaped + r'(?!\w)', normalized))


def find_candidates(curriculum_path: str | Path, aliases_path: str | Path) -> list[dict[str, str]]:
    aliases = load_aliases(aliases_path)
    by_skill = defaultdict(list)
    for phrase, alias_info in aliases.items():
        by_skill[alias_info.canonical_skill].append((phrase, alias_info.reviewed_by))
    for skill in by_skill:
        by_skill[skill].sort(key=lambda pair: (-len(pair[0]), pair[0]))

    rows = []
    with Path(curriculum_path).open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(column not in reader.fieldnames for column in REQUIRED):
            raise ValueError(f'{curriculum_path}: missing expected curriculum columns')
        for topic in reader:
            if topic['analysis_group'] != 'PRIMARY_2025_2026':
                continue  # historical CS317 is a separate research artifact
            if topic['source_verification_status'] == 'UNSUPPORTED':
                continue
            for canonical, phrases in sorted(by_skill.items()):
                match = None
                # Topic text is stronger evidence than the derived skill-concept field.
                for evidence_field in ('topic_text', 'skill_concept_candidate'):
                    text = topic[evidence_field] or ''
                    for phrase, reviewed_by in phrases:
                        if literal_phrase_present(phrase, text):
                            match = (phrase, reviewed_by, evidence_field)
                            break
                    if match:
                        break
                if not match:
                    continue
                phrase, reviewed_by, evidence_field = match
                interpretation = (
                    'Literal mention in research topic text; human review required. '
                    'A webpage reading list is not evidence of actual instruction or mastery.'
                    if evidence_field == 'topic_text' else
                    'Literal mention only in researcher-assigned skill concept; '
                    'not an original syllabus quote. Human source review required.'
                )
                rows.append({
                    'curriculum_id': topic['curriculum_id'],
                    'canonical_skill': canonical,
                    'course_id': topic['course_id'],
                    'topic_id': topic['topic_id'],
                    'topic_text': topic['topic_text'],
                    'matched_phrase': phrase,
                    'evidence_field': evidence_field,
                    'match_method': 'exact' if phrase == canonical else 'alias',
                    'source_verification_status': topic['source_verification_status'],
                    'curriculum_review_status': topic['review_status'],
                    'alias_reviewed_by': reviewed_by,
                    'source_url': topic['source_url'],
                    'source_locator': topic['source_locator'],
                    'source_page': topic['source_page'],
                    'evidence_scope': topic['evidence_scope'],
                    'coverage_status': 'unknown',
                    'coverage_score': '',
                    'interpretation': interpretation,
                })
    return sorted(rows, key=lambda r: (r['canonical_skill'], r['course_id'], r['topic_id']))


def write_candidates(rows: list[dict[str, str]], output: str | Path) -> None:
    """Write a new audit only; refuse to overwrite any output or input file."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--curriculum', required=True, type=Path)
    parser.add_argument('--aliases', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.resolve() in {args.curriculum.resolve(), args.aliases.resolve()}:
        parser.error('Output must be separate from input files')
    try:
        rows = find_candidates(args.curriculum, args.aliases)
        write_candidates(rows, args.output)
    except (OSError, ValueError) as exc:
        print(f'A-03 screening error: {exc}', file=sys.stderr)
        return 1
    print(f'Wrote {len(rows)} provisional literal-match candidates to {args.output}')
    print('All coverage statuses are unknown; this is not an approved coverage assessment.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
