# A-06 — Provisional Scientific-Integrity Validation

A-06 adds tests and an independent runner to check **input/output provenance**, **whole-phrase matching**, **primary-vs-historical corpus isolation**, **tamper detection**, **deterministic replays** and the boundary between *literal candidate detection* and *verified curriculum coverage*.

This does **not** validate that the source website is factual, that an unreviewed alias is scientifically correct, that a skill is taught or missing, or that job observations represent the market. A-05's genuine precision/recall/F1 metrics remain unavailable until independent human review of all ten skills.

From the repository root, after extracting files, run tests:

```bash
python -B -m pytest -v -p no:cacheprovider
```

To generate an optional, new provenance/reproducibility report from the existing *source inputs* (not from possibly stale files in `/tmp`):

```bash
python -B -m validation.scientific_checks --curriculum data/processed/curriculum_topics.csv --aliases data/reference/skill_aliases.csv --snapshot outputs/skill_snapshot_2026-11-22.csv --output /tmp/skilldrift_a06_validation_v0.json
```

- This recomputes A-03 and A-04 artifacts in an isolated temporary folder, uses A-05 to check the blind human-review template, then cleans up temporary files.
- It reverses the input CSV row order and ensures matching/audit results are identical; compares serialized CSV SHA-256 hashes, and records input hashes for reproducibility.
- Only the new JSON file is written to the requested output path; existing outputs are **not** overwritten, and `main` and teammates' code are untouched.
- Every candidate is checked against the declared primary topic and evidence field, phrase, alias table, and source locator. This validates internal provenance only: it does not independently check external website contents.
- The JSON has `real_evaluation_metrics_available: false` and does **not** include accuracy or inferred coverage/gap scores.

The tests use synthetic fixture curriculum/snapshot rows and are not real student, syllabus, or market evaluation observations. A-03, A-04, and A-05 remain provisional and subject to D-003/D-006/team approval. Review tests and schemas with both owners before integrating or merging.
