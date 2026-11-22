"""A-02 (provisional): conservative, traceable normalization of source skill tags.

This module normalizes *explicit CSV skills tags*, not shortened job-description
text and not inferred curriculum coverage. It never changes the ten historic
snapshot labels or files. Unknown tags are retained as unmatched records.

Usage from repo root (no third-party dependencies):
  python3 -m nlp.normalize_skills \
      --aliases data/reference/skill_aliases.csv \
      --skills 'PySpark, SQL, Apache Airflow, Spark, Data Warehousing'

  python3 -m nlp.normalize_skills \
      --aliases data/reference/skill_aliases.csv \
      --input-csv path/to/audited_jobs.csv \
      --output-csv /tmp/skill_normalization_audit.csv

No original job/snapshot CSV is edited. The input CSV must include `skills`.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import sys
import unicodedata

REQUIRED_ALIAS_COLUMNS = ('alias', 'canonical_skill', 'category', 'reviewed_by', 'notes')
AUDIT_COLUMNS = ('source_row_number', 'raw_tag', 'lookup_key', 'canonical_skill',
                 'match_method', 'matched')


def lookup_key(value: str) -> str:
    """Canonicalize only whitespace/case/Unicode; no semantic guessing."""
    if not isinstance(value, str):
        raise TypeError('Skill tag must be text')
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().strip().split())


@dataclass(frozen=True)
class AliasInfo:
    canonical_skill: str
    category: str
    reviewed_by: str
    notes: str


@dataclass(frozen=True)
class TagMatch:
    raw_tag: str
    lookup_key: str
    canonical_skill: str | None
    match_method: str

    @property
    def matched(self) -> bool:
        return self.canonical_skill is not None


def load_aliases(path: str | Path) -> dict[str, AliasInfo]:
    """Read a reviewed alias table; conflicting normalized keys are errors."""
    path = Path(path)
    with path.open('r', newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or any(col not in reader.fieldnames for col in REQUIRED_ALIAS_COLUMNS):
            raise ValueError(f'{path}: expected columns {", ".join(REQUIRED_ALIAS_COLUMNS)}')
        index: dict[str, AliasInfo] = {}
        for row_number, row in enumerate(reader, start=2):
            alias = lookup_key(row['alias'] or '')
            canonical = lookup_key(row['canonical_skill'] or '')
            if not alias or not canonical:
                raise ValueError(f'{path}:{row_number}: blank alias or canonical_skill')
            value = AliasInfo(canonical_skill=canonical,
                              category=(row['category'] or '').strip(),
                              reviewed_by=(row['reviewed_by'] or '').strip(),
                              notes=(row['notes'] or '').strip())
            if alias in index and index[alias].canonical_skill != canonical:
                raise ValueError(f'{path}:{row_number}: ambiguous alias {alias!r} maps to both '
                                 f'{index[alias].canonical_skill!r} and {canonical!r}')
            index[alias] = value
    return index


def normalize_tag(raw_tag: str, aliases: dict[str, AliasInfo]) -> TagMatch:
    """Return explicit exact/alias match, otherwise UNMATCHED; no substring search."""
    key = lookup_key(raw_tag)
    found = aliases.get(key)
    if not found:
        return TagMatch(raw_tag=raw_tag, lookup_key=key,
                        canonical_skill=None, match_method='unmatched')
    method = 'exact' if key == found.canonical_skill else 'alias'
    return TagMatch(raw_tag=raw_tag, lookup_key=key,
                    canonical_skill=found.canonical_skill, match_method=method)


def normalize_skill_tags(skills_field: str, aliases: dict[str, AliasInfo]) -> list[TagMatch]:
    """Source `skills` field is defined as comma-delimited; preserve each raw tag."""
    if not isinstance(skills_field, str):
        raise TypeError('skills_field must be text')
    return [normalize_tag(tag.strip(), aliases) for tag in skills_field.split(',')
            if lookup_key(tag)]


def audit_input_csv(input_csv: str | Path, output_csv: str | Path,
                    aliases: dict[str, AliasInfo]) -> int:
    """Produce a NEW tag-audit file; never modify the input CSV."""
    input_csv, output_csv = Path(input_csv), Path(output_csv)
    if input_csv.resolve() == output_csv.resolve():
        raise ValueError('Output path must differ from input path')
    if output_csv.exists():
        raise FileExistsError(f'Output exists; choose a new path: {output_csv}')
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with input_csv.open('r', newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or 'skills' not in reader.fieldnames:
            raise ValueError(f'{input_csv}: missing required skills column')
        with output_csv.open('x', newline='', encoding='utf-8') as target:
            writer = csv.DictWriter(target, fieldnames=AUDIT_COLUMNS, lineterminator='\n')
            writer.writeheader()
            for source_row_number, source_row in enumerate(reader, start=1):
                for result in normalize_skill_tags(source_row.get('skills') or '', aliases):
                    writer.writerow({
                        'source_row_number': source_row_number,
                        'raw_tag': result.raw_tag,
                        'lookup_key': result.lookup_key,
                        'canonical_skill': result.canonical_skill or '',
                        'match_method': result.match_method,
                        'matched': str(result.matched).lower(),
                    })
                    count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aliases', required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--skills', help='Comma-separated source skills field')
    mode.add_argument('--input-csv', type=Path, help='Input CSV with a skills column')
    parser.add_argument('--output-csv', type=Path, help='New output path in CSV audit mode')
    opts = parser.parse_args(argv)
    try:
        index = load_aliases(opts.aliases)
        if opts.skills is not None:
            if opts.output_csv is not None:
                parser.error('--output-csv is for --input-csv mode only')
            for result in normalize_skill_tags(opts.skills, index):
                canonical = result.canonical_skill or '<unmatched>'
                print(f'{result.raw_tag!r} -> {canonical} [{result.match_method}]')
        else:
            if opts.output_csv is None:
                parser.error('--output-csv is required with --input-csv')
            n = audit_input_csv(opts.input_csv, opts.output_csv, index)
            print(f'Wrote {n} tag-level audit rows to {opts.output_csv}')
    except (OSError, ValueError, TypeError) as error:
        print(f'Normalization error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
