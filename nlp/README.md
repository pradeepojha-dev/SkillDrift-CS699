# A-02: Skill tag normalization (provisional module)

This zero-dependency Python module maps **only whole, explicit, comma-delimited** source `skills` tags via `data/reference/skill_aliases.csv` to the project's original ten historical skill labels. It is not a skill extractor from truncated descriptions and does not infer curriculum coverage.

From repository root:

```bash
python3 -m nlp.normalize_skills --aliases data/reference/skill_aliases.csv --skills 'PYTHON, SQL, Apache Airflow, Spark'
```

Expected: `python`, `sql`, `airflow`, then `<unmatched>` for `Spark` (not automatically `PySpark`).

For a **new audit file**, never an original dataset:

```bash
python3 -m nlp.normalize_skills --aliases data/reference/skill_aliases.csv --input-csv path/to/input_with_skills.csv --output-csv /tmp/skill_normalization_audit.csv
```

The audit carries `source_row_number`, unaltered tag string, normalized lookup key, canonical skill (empty for unknown), and exact/alias/unmatched method. The CSV `reviewed_by` entries explicitly say `PENDING_HUMAN_REVIEW`. No alias implies tool mastery or course content. Do not merge new normalized job-demand calculations into the historical ten-skill snapshots without an approved versioned schema.
