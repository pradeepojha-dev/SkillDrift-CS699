# A-01: Evidence-linked selected-course curriculum sample (provisional)

This is an **assistant-reviewed manual source mapping**, not a full IIT Bombay CSE curriculum extraction, not proof students learned listed skills, and not a substitute for a human academic review.

- `../data/processed/curriculum_topics.csv`: only 2025–26 **selected sources** (CS215, CS631, CS632, CS725), 45 source-supported or explicitly uncertain records; no CS317 or unsupported CS725/Python row.
- `../data/processed/curriculum_topics_historical_cs317.csv`: historical proposed 2008 curriculum, 10 records, PDF physical page 14.
- `reviews/candidate_row_verification.csv`: all 56 original candidate mappings, corrections, evidence scopes, and verdicts.
- `VERIFICATION_REPORT.md`: source links, methodology, material limitations and pending contracts.

**Status distinction:** `source_verification_status=VERIFIED|UNCERTAIN|UNSUPPORTED` means documentary traceability assessment. `review_status=unreviewed|approved|rejected` is the **separate proposed C-04 human review field**, currently `unreviewed` throughout. For HTML, `source_page` is blank; use `source_locator`. Only the historical PDF has a verified physical page number.

All additional C-04 columns and `curriculum_id` values are provisional until joint approval. Do not overwrite historical data; do not treat unsupported/uncertain/reading-list-only claims as confirmed taught skill coverage.
