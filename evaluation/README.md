# A-05 — Provisional Human-Labeled Evaluation

This evaluator is **not** an approved curriculum coverage assessment. It benchmarks whether A-03 flagged **at least one relevant literal mention per canonical skill** in the selected primary curriculum topic fields; this is narrower than whether the skill is actually taught. The ten-skill benchmark contains only the fixed SkillDrift skill labels. No real accuracy/precision/recall scores may be stated until independently reviewed reference labels exist.

## Workflow (repository root)

Prerequisite: Generate the provisional A-03 and A-04 CSVs as documented in their modules.

1. Generate a *blinded* ten-skill human reference-label template. It has no predicted values or prefilled answers:

   ```bash
   python -B -m evaluation.evaluate prepare --audit /tmp/skilldrift_a04_gap_audit_v0.csv --candidates /tmp/skilldrift_a03_candidates_v0.csv --output /tmp/skilldrift_a05_manual_labels_v0.csv
   ```

2. Human reviewer examines **every primary curriculum row** (including `topic_text` and the explicitly derived `skill_concept_candidate` field) for **all ten skills**, without using A-03 predictions to decide answers. Fill the template's `reference_label` (`present`/`absent`), `reviewer`, `review_date` (`YYYY-MM-DD`) and `manual_evidence` (specific source/topic references for positives; documented full corpus review scope for negatives). `review_notes` is optional. All ten skills must have complete labels. Manual labels are **not** automatically created by this tool.

3. With a genuinely independently reviewed reference template, score it:

   ```bash
   python -B -m evaluation.evaluate score --audit /tmp/skilldrift_a04_gap_audit_v0.csv --candidates /tmp/skilldrift_a03_candidates_v0.csv --labels /tmp/skilldrift_a05_manual_labels_v0.csv --output /tmp/skilldrift_a05_eval_report_v0.json
   ```

No output path may overwrite an existing file. Both modes check A-03/A-04 skill counts and evidence provenance. Score mode *refuses incomplete labels*. All unit-test labels are **synthetic test fixtures only** and not project evaluation evidence.

## Metrics / limitations

- TP: A-03 found >=1 candidate and human found >=1 relevant literal mention.
- FP: A-03 found >=1 candidate but human found no relevant literal mention.
- FN: A-03 found none but human found >=1 relevant literal mention.
- TN: A-03 found none and human found no relevant literal mention.
- Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). If denominator is zero, metric is `null`, not a fabricated zero.
- All these numbers apply **at skill level** to only ten preselected industry skills, not to individual topic-skill candidate rows. Thus false positives at the *candidate* level can remain undetected in this benchmark. Future candidate-level adjudication is needed for row-level precision.
- They do NOT measure confirmed teaching, mastery, curriculum skill gaps, general employment demand, or any population-wide trend. A-03 and A-04 preserve `unknown` / `NOT_ASSESSABLE` coverage and gap results.
- This implementation and any evaluation protocol or output schema remain provisional until both owners approve the relevant shared decisions.
