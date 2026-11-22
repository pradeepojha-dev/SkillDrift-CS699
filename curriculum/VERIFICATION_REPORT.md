# SkillDrift CS699 — A-01 source verification report

**Prepared:** 2026-11-22 (IST)<br>
**Owner lane:** Abhay Patle / `abhyqan`<br>
**Review basis:** `SkillDrift_IITB_Curriculum_A01_Pack.zip`, its **56-row candidate** CSV, and the **five live official IIT Bombay CSE pages/PDF**.<br>
**State:** **Provisional source-based review**, not a jointly approved curriculum coverage or completed-course claim. No job data, snapshots, API data, gap scores or existing repository files were changed.

## Definitions — read before interpreting counts

- **VERIFIED**: the stated topic/tool/concept is named or faithfully paraphrased in the *specified official source*. For CS632, this proves only that a research-paper **reading-list topic** appears, **not** that a lecture, lab or assessment actually covered it. For tentative schedules, it confirms a listed plan, **not** delivery.
- **UNCERTAIN**: a related heading or indirect indication exists, but evidence is insufficient for the specific mapping.
- **UNSUPPORTED**: the named official source does not substantiate the candidate claim; exclude from source-supported analysis. This **does not mean the institution does not teach the skill**.
- `review_status=unreviewed` in the proposed C-04 schema is deliberately separate: **no human academic approval is claimed**. Assistant verification is represented in extra `source_verification_status` column. Human review/contract sign-off can change either.

## Row-by-row review results

| Course | Source offering | Candidate | VERIFIED | UNCERTAIN | UNSUPPORTED | In primary CSV | In historical CSV |
|---|---|---:|---:|---:|---:|---:|---:|
| CS215 | Autumn 2025 | 10 | 10 | 0 | 0 | 10 | 0 |
| CS631 | Autumn 2026 | 12 | 12 | 0 | 0 | 12 | 0 |
| CS632 | Spring 2026 | 10 | 9 | 1 | 0 | 10 | 0 |
| CS725 | Autumn 2026 | 14 | 13 | 0 | 1 | 13 | 0 |
| CS317 | **Historical proposed 2008** | 10 | 10 | 0 | 0 | 0 | 10 |
| **TOTAL** | | **56** | **54** | **1** | **1** | **45** | **10** |

All 56 original row numbers and the review findings are retained in `curriculum/reviews/candidate_row_verification.csv`. The **primary** working CSV contains 45 *source-supported or explicitly uncertain* rows from four 2025–2026 sources; 44 of those 45 are VERIFIED. **Do not use the one UNCERTAIN row as proven coverage.** The 10 CS317 rows remain in a separate historical file. The one UNSUPPORTED row remains only in the audit.

## Official sources and evidence limitations

1. **CS215** — *Data Interpretation and Analysis*, **Autumn 2025**. Actual page title changed from draft's “Data Analysis and Interpretation.” Verified against computational resources and dated lecture schedule, including MATLAB, probability, MLE, least squares, KDE, testing, and multivariate Gaussians. Official source: https://www.cse.iitb.ac.in/~ajitvr/CS215_Fall2025/<br>
2. **CS631** — *Implementation techniques in DBMS*, **Autumn 2026**. Corrected draft's longer title. Course contents and **tentative** lecture schedule list PostgreSQL assignments, storage, indexing, query optimization, transactions, big data, and parallel/distributed systems. The selected page does not establish PySpark or vendor cloud skills. Official source: https://www.cse.iitb.ac.in/infolab/Data/Courses/CS631/CS631.html<br>
3. **CS632** — *Advanced DBMS*, **Spring 2026**. Corrected draft's longer title. This page explicitly calls the paper/topic list changeable; therefore all rows use `evidence_scope=reading_list_only`. Paper titles are not proof that topics were actually delivered or students can use the tools. Official source: https://www.cse.iitb.ac.in/infolab/Data/Courses/CS632/<br>
4. **CS725** — *Foundations of Machine Learning*, **Autumn 2026**. The official calendar names core ML algorithms, neural networks, CNN, RNN, Transformers, PCA, clustering and foundation models for text. Its official homepage/calendar **do not name Python**; the draft row asserting “Programming assignments require Python” is **UNSUPPORTED against these selected official pages**. This is not proof Python was absent from private Moodle, labs or assignments. Calendar: https://www.cse.iitb.ac.in/~sunita/cs725/calendar.html ; offering homepage: https://www.cse.iitb.ac.in/~sunita/cs725/<br>
5. **CS317** — *Database and Information Systems*, **historical 2008 proposed UG curriculum**, **not** a current 2026 offering. Original syllabus appears on **physical PDF page 14 (1-based; zero-indexed page 13)**, visually inspected. SQL, normalization, relational algebra, data warehousing etc. are source-supported **historical** claims. Official PDF: https://www.cse.iitb.ac.in/~br/dugc/curriculum/ugcurriculum08.pdf<br>

The research pack's `CURRICULUM_SOURCE_DOSSIER.pdf` was a **researcher-authored synthesis**, not an official IITB syllabus. Its `Dossier Page` is not a valid original source page. HTML sources use a blank `source_page` and a clear `source_locator`; CS317 uses `source_page=14`.

## Material corrections and uncertainty

- **Row 33 (CS725/Python): UNSUPPORTED**; excluded from the primary CSV. Do not claim Python was explicitly taught or required from this public source.
- **Row 30 (CS632/data cleaning): UNCERTAIN**; heading contains “Data cleaning” but the specific displayed papers concentrate on functional dependencies, so only heading-level evidence exists. Included for audit, **not affirmative curriculum coverage**.
- **Row 25 (CS632):** “Vector indexing” narrowed to *Graph-based ANN search*, which is directly traceable to graph-based ANN papers.
- **Row 35 (CS725):** the original broad “Regression modelling” refined to *Linear regression and logistic classification* to distinguish the distinct calendar items.
- **Row 41 (CS725):** both CNN and RNN are explicitly calendar topics, but are **not mapped automatically** to one job-taxonomy label.
- **Row 46 (CS725):** vague “LLM fundamentals” narrowed to *Foundation models for text* per source heading.
- **Row 49 (CS215):** broad “Data visualization” narrowed to *Statistical plotting and histograms*.
- **Row 56 (CS215):** broad “Multivariate statistics” narrowed to *Multivariate Gaussian distributions*.
- **Rows 16, 18, 22 (CS631):** topic text narrowed to exactly the published schedule; terms such as “serializability” and “crash/failure” were not asserted as explicit scheduled labels.
- **Rows 1–10 (CS317):** original source-page placeholder replaced with **14**; historical boundary enforced.
- **CS215, CS631 and CS632:** corrected course titles to official published page titles.

The full audit is the authoritative row-by-row change log; do not treat this selective list as exhaustive row-level evidence.

## Dataset and analysis eligibility

- Proposed primary sample: **four selected courses** (CS215 2025, CS631/CS725 Autumn 2026, CS632 Spring 2026). Not a full departmental, graduate or institutional syllabus. Selection biases are substantial.
- CS632 entries only represent **reading-list inclusion**, not confirmed taught content.
- The source-based verification does **not** establish that a job tool was taught, student proficiency, complete coverage, or an absent skill. Absence of mention in these selected sources means `unknown`, **not** “missing” across IITB.
- The existing ten SkillDrift job-skill tags are independent from rich curriculum concepts; do not map PostgreSQL → SQL, parallel query processing → PySpark, data warehousing → ETL, or generically “cloud” → AWS/GCP/Azure Data Factory.
- **No gap scores are calculated.** A-03 matching and A-04 scoring await the D-003 schema/unknown semantics and D-006/D-007 human-approved rules. Changing the existing ten labels or ±5 pp rule requires an approved version change.

## File contract — provisional only

- `data/processed/curriculum_topics.csv`: 45 rows, C-04's nine proposed required columns **plus provenance/review extensions**, four modern-course sample, **no CS317 or unsupported Python**.
- `data/processed/curriculum_topics_historical_cs317.csv`: 10 rows, same schema, separate 2008 source.
- `curriculum/reviews/candidate_row_verification.csv`: 56 rows, original vs revised mapping, verdict and explanation.
- `data/reference/skill_aliases.csv`: 26 proposed aliases over the **unchanged original ten** canonical skill labels; every `reviewed_by=PENDING_HUMAN_REVIEW`.
- `nlp/normalize_skills.py`: standalone A-02 draft, exact/alias-only matching of comma-separated explicit skill tags. Unknown values retained; no semantic inference, no source datasets overwritten.
- `tests/test_curriculum.py`, `tests/test_normalize_skills.py`: local integrity/unit tests, **not independent scientific validation**.

`curriculum_id` values are **provisional internal IDs**, not user-approved titles; `extraction_method=manual` represents actual source-by-source inspection (not OCR or automated PDF extraction). The C-04 schema remains a **proposal** until D-003 is approved; do not integrate the output with Pradeep's API as a frozen contract yet.

## Open decisions that materially affect validity

1. **D-003, C-04:** approve/revise fields (especially extra `source_url`, `course_offering`, `source_verification_status`, `evidence_scope`) and precise meaning of `review_status` before main/API integration.
2. **D-005:** formalize the four-course provisional primary sample and the CS317 historical-only exclusion in a joint decision record.
3. **D-006/D-007:** approve what counts as partial coverage, how reading-list-only/uncertain evidence is treated, what constitutes missing vs unknown, and weighting. The current review does not pre-approve those choices.
4. **A-02 alias signoff:** proposed synonyms need a second human review before being applied to demand snapshots, which must remain unchanged unless explicitly versioned.
5. **SYNC:** D-001 human approval is reported, but its GitHub documentation update is pending. Git `main` SHA was reported as `557837be3488ee4e4eb355714d61fcebd9df3918`; this workspace has **no current repository checkout**, so the remote SHA and absence of conflicting files cannot be verified. **No branch, commit or PR created.**

## Reproducible checks

From a *separate branch after inspecting actual repository files for collisions*, copy the supplied file paths into the repo. Then from the repo root:

```bash
python3 -m unittest discover -s tests -p 'test_curriculum.py' -v
python3 -m unittest discover -s tests -p 'test_normalize_skills.py' -v
python3 -m nlp.normalize_skills --aliases data/reference/skill_aliases.csv --skills 'Python, Apache Airflow, Spark, Data Warehousing'
```

Review the full 56-row audit with a human before changing `review_status` from `unreviewed` to `approved`, making final curriculum-coverage claims, or connecting the data to the gap API.
