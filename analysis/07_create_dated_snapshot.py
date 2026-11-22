"""SkillDrift: create one genuine, date-specific skill-demand snapshot.

Uses the SAME skill-cleaning and demand calculation as analysis/05_compare_skills.py:
- lowercase + strip
- exclude exactly the four original noise terms
- count each skill at most once per job
- job demand percentage = 100 * jobs containing skill / jobs sampled

Run from the SkillDrift-CS699 project folder:
    python analysis/07_create_dated_snapshot.py

This script deliberately does not change existing programs, graphs, or old snapshots.
"""

from collections import Counter
from pathlib import Path
import sys

import pandas as pd

COLLECTION_DATE = "2026-11-22"
CITIES = ("mumbai", "pune", "bengaluru")
SKILLS_TO_COMPARE = (
    "python", "sql", "pyspark", "snowflake", "aws", "airflow",
    "azure data factory", "gcp", "etl", "data pipelines",
)
NOISE_WORDS = {"data", "senior", "data engineer", "data engineering"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FOLDER = PROJECT_ROOT / "data" / "raw"
OUTPUT_FOLDER = PROJECT_ROOT / "outputs"
OUTPUT_FILE = OUTPUT_FOLDER / f"skill_snapshot_{COLLECTION_DATE}.csv"


def read_city(city):
    csv_path = RAW_FOLDER / f"naukri_data_engineering_{city}_{COLLECTION_DATE}.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing exact dated file: {csv_path}")

    data = pd.read_csv(csv_path, encoding="utf-8-sig")
    if "skills" not in data.columns:
        raise ValueError(f"Missing 'skills' column in {csv_path.name}")
    if data.empty:
        raise ValueError(f"No job rows in {csv_path.name}")

    counts = Counter()
    for skills_text in data["skills"].fillna("").astype(str):
        unique_skills = {
            skill.strip().lower()
            for skill in skills_text.split(",")
            if skill.strip() and skill.strip().lower() not in NOISE_WORDS
        }
        counts.update(unique_skills)

    print(f"{city.title():10s}: {len(data):2d} jobs | {csv_path.name}")
    return len(data), counts


def main():
    print("\nSKILLDRIFT — DATE-SPECIFIC SKILL SNAPSHOT")
    print(f"Collection date: {COLLECTION_DATE}\n")

    stats = {city: read_city(city) for city in CITIES}

    rows = []
    for skill in SKILLS_TO_COMPARE:
        row = {"Date": COLLECTION_DATE, "Skill": skill}
        for city in CITIES:
            job_count, skill_counts = stats[city]
            row[f"{city.title()} %"] = round(
                skill_counts.get(skill, 0) / job_count * 100, 1
            )
        rows.append(row)

    result = pd.DataFrame(rows, columns=[
        "Date", "Skill", "Mumbai %", "Pune %", "Bengaluru %"
    ])

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        if existing.equals(result):
            print(f"\nAlready exists with identical contents: {OUTPUT_FILE.name}")
            print("No file changed.")
            return
        raise FileExistsError(
            f"Refusing to overwrite a different existing snapshot: {OUTPUT_FILE}"
        )

    result.to_csv(OUTPUT_FILE, index=False)
    print("\n" + result.to_string(index=False))
    print(f"\nSUCCESS: Saved {OUTPUT_FILE}")
    print("October snapshot and old regional outputs were not modified.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, FileExistsError) as error:
        print(f"\nSTOP: {error}", file=sys.stderr)
        raise SystemExit(1)
