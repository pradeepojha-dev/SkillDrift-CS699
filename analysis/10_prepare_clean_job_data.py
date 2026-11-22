"""SkillDrift CS699 / P-01: Prepare non-destructive, row-preserving job samples.

Run from anywhere: python analysis/10_prepare_clean_job_data.py
Uses only Python standard library. Does NOT modify data/raw or outputs/snapshots.

Produces six files data/processed/job_samples_<city>_<date>.csv (same nine columns)
and outputs/audit/cleaning_summary.csv.

Cleaning policy:
* Strip leading/trailing whitespace in source text fields.
* Strip whitespace around comma-separated skill tags, remove repeated tags within
  the SAME source row (case-insensitively), and preserve original order/spelling.
* Never invent missing URLs, remove missing-URL records, or merge city results.
* Do not infer aliases/skill taxonomies: they are Abhay's separate NLP task.
* Keep descriptions unchanged apart from leading/trailing whitespace.
"""

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
AUDIT = ROOT / "outputs" / "audit"
DATES = ("2026-10-15", "2026-11-22")
CITIES = ("mumbai", "pune", "bengaluru")
COLUMNS = (
    "title", "company", "experience", "salary", "location",
    "description", "posted", "skills", "url",
)


def clean_skills(raw):
    seen = set()
    cleaned = []
    removed = 0
    for item in (raw or "").split(","):
        tag = " ".join(item.split())
        if not tag:
            continue
        key = tag.casefold()
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        cleaned.append(tag)
    return ", ".join(cleaned), removed


def main():
    # Validate all inputs before writing outputs.
    inputs = []
    for date in DATES:
        for city in CITIES:
            filename = f"naukri_data_engineering_{city}_{date}.csv"
            source = RAW / filename
            if not source.is_file():
                raise FileNotFoundError(f"Missing raw dataset: {source}")
            with source.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames != list(COLUMNS):
                    raise ValueError(
                        f"Unexpected schema in {filename}: {reader.fieldnames!r}"
                    )
                rows = list(reader)
            inputs.append((date, city, filename, rows))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    summary = []
    total = Counter()

    for date, city, filename, rows in inputs:
        processed_rows = []
        repeated_removed = 0
        missing_urls = 0
        for row in rows:
            output = {key: (row.get(key) or "").strip() for key in COLUMNS}
            output["skills"], count = clean_skills(output["skills"])
            repeated_removed += count
            missing_urls += not bool(output["url"])
            processed_rows.append(output)

        out = PROCESSED / f"job_samples_{city}_{date}.csv"
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(processed_rows)

        # Sanity check output row counts and field order.
        with out.open("r", encoding="utf-8", newline="") as handle:
            check = csv.DictReader(handle)
            if check.fieldnames != list(COLUMNS) or sum(1 for _ in check) != len(rows):
                raise RuntimeError(f"Output validation failed: {out}")

        summary.append({
            "date": date,
            "city": city,
            "source_file": filename,
            "processed_file": out.relative_to(ROOT).as_posix(),
            "source_rows": len(rows),
            "processed_rows": len(processed_rows),
            "missing_url_preserved": int(missing_urls),
            "repeated_skill_tags_removed": repeated_removed,
        })
        total[date] += len(rows)
        print(
            f"{date} | {city:9s} | kept {len(rows):2d}/{len(rows):2d} rows | "
            f"missing URLs kept={missing_urls} | repeated tags removed={repeated_removed}"
        )

    report = AUDIT / "cleaning_summary.csv"
    with report.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    print(f"\nTotals preserved: October={total['2026-10-15']}, November={total['2026-11-22']}")
    print("No rows deleted, no URLs invented, no city records merged.")
    print("Existing snapshots are untouched; historical results remain as originally calculated.")
    print("SUCCESS: six cleaned copies in data/processed/")
    print(f"SUCCESS: {report.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
