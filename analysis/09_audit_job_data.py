"""SkillDrift P-01: non-destructive audit of six dated Naukri CSV samples.

From repository root:  python analysis/09_audit_job_data.py
Requires Python 3.8+; only uses the standard library.
Does not edit raw files, snapshots, or previous team contributions.
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "outputs" / "audit"
DATES = ("2026-10-15", "2026-11-22")
CITIES = ("mumbai", "pune", "bengaluru")
COLUMNS = (
    "title", "company", "experience", "salary", "location",
    "description", "posted", "skills", "url",
)
REQUIRED = ("title", "company", "skills", "url")


def get_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        missing_columns = [name for name in COLUMNS if name not in columns]
        if missing_columns:
            raise ValueError(f"{path.name}: missing columns: {missing_columns}")
        rows = list(reader)
    return rows


def normalized_url(value):
    # Remove tracking query and trailing slash, without modifying original records.
    text = (value or "").strip()
    try:
        parsed = urlsplit(text)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ""
        return (parsed.netloc.lower() + parsed.path.rstrip("/")).lower()
    except ValueError:
        return ""


def add_issue(issues, date, city, row, severity, code, details, url=""):
    issues.append({
        "date": date, "city": city, "csv_row": row,
        "severity": severity, "issue": code,
        "details": details, "url": url,
    })


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    issues = []
    report_lines = ["SkillDrift | Job data-quality audit", "Raw input: six dated city CSVs (unchanged)", ""]
    totals = Counter()
    url_locations = defaultdict(list)

    for date in DATES:
        for city in CITIES:
            path = RAW_DIR / f"naukri_data_engineering_{city}_{date}.csv"
            if not path.exists():
                raise FileNotFoundError(f"Missing input: {path}")
            rows = get_rows(path)
            totals[date] += len(rows)
            seen_urls = {}
            blanks = Counter()
            for row_number, row in enumerate(rows, start=2):
                url = (row.get("url") or "").strip()
                key = normalized_url(url)
                for column in COLUMNS:
                    if not (row.get(column) or "").strip():
                        blanks[column] += 1
                for column in REQUIRED:
                    if not (row.get(column) or "").strip():
                        add_issue(issues, date, city, row_number, "WARNING", "MISSING_REQUIRED", f"Empty {column}", url)
                if url and not key:
                    add_issue(issues, date, city, row_number, "WARNING", "INVALID_URL", "Not a valid HTTP(S) URL", url)
                if key:
                    if key in seen_urls:
                        add_issue(issues, date, city, row_number, "WARNING", "DUPLICATE_WITHIN_CITY", f"Same job URL as CSV row {seen_urls[key]}", url)
                    else:
                        seen_urls[key] = row_number
                    url_locations[(date, key)].append((city, row_number, url))
                tokens = [value.strip().lower() for value in (row.get("skills") or "").split(",") if value.strip()]
                if len(tokens) != len(set(tokens)):
                    add_issue(issues, date, city, row_number, "INFO", "REPEATED_SKILL_TAG", "Repeated skills after case normalization", url)
                if (row.get("description") or "").strip().endswith("..."):
                    add_issue(issues, date, city, row_number, "INFO", "TRUNCATED_DESCRIPTION", "Description appears abbreviated", url)
            report_lines.append(f"{date} | {city:<9} | jobs={len(rows):>2} | missing: " +
                                (", ".join(f"{k}={v}" for k, v in blanks.items()) or "none"))

    overlap_groups = 0
    for (date, _), occurrences in sorted(url_locations.items()):
        cities = sorted({city for city, _, _ in occurrences})
        if len(cities) > 1:
            overlap_groups += 1
            city_rows = ", ".join(f"{city} row {row}" for city, row, _ in occurrences)
            add_issue(issues, date, "/".join(cities), "", "INFO", "CROSS_CITY_OVERLAP",
                      "Same job listed in multiple city samples: " + city_rows, occurrences[0][2])

    issue_counts = Counter(i["issue"] for i in issues)
    report_lines.extend([
        "", f"October city-result rows: {totals['2026-10-15']}",
        f"November city-result rows: {totals['2026-11-22']}",
        f"Cross-city overlapping job URLs (per date): {overlap_groups}",
        "", "Issue totals:",
    ])
    report_lines.extend(f"  {key}: {value}" for key, value in sorted(issue_counts.items()))
    report_lines.extend([
        "", "Notes:",
        "- An empty salary is common and is not treated as an invalid job.",
        "- Cross-city repeats are informational; they are not necessarily duplicates within a city.",
        "- The unit of analysis is a city-search result, not necessarily a globally unique job.",
        "- This audit does NOT clean, deduplicate, normalize, or alter existing data or snapshots.",
        "- Small samples cannot establish population-level industry trends.",
    ])

    csv_path = REPORT_DIR / "job_quality_issues.csv"
    txt_path = REPORT_DIR / "job_quality_summary.txt"
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "city", "csv_row", "severity", "issue", "details", "url"])
        writer.writeheader()
        writer.writerows(issues)
    txt_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("\n".join(report_lines))
    print(f"\nSUCCESS: {csv_path.relative_to(ROOT)}")
    print(f"SUCCESS: {txt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
