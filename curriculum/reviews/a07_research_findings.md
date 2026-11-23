# A-07: Human Curriculum and Skill-Mapping Validation

**Report date:** 2026-11-23
**Project:** SkillDrift — IIT Bombay CS699
**Review owner:** Abhay Patle
**Research status:** Provisional documentary validation

## 1. Objective

Review the selected curriculum dataset, verify source evidence, and audit provisional literal skill mentions.

This work does not establish whether particular skills were taught, mastered, or absent from a curriculum.

## 2. Dataset and Methodology

- Selected primary curriculum records: 45.
- Courses examined: CS215, CS631, CS632 and CS725.
- Historical CS317 records are excluded.
- Each curriculum record was reviewed against its documented source.
- Results were stored in a separate A-07 human-review CSV.
- Provisional literal skill matches were checked independently against source evidence.
- The original processed curriculum dataset was not modified by this workflow.

## 3. Curriculum Validation Results

| Course | Reviewed | Total |
|---|---:|---:|
| CS215 | 10 | 10 |
| CS631 | 12 | 12 |
| CS632 | 10 | 10 |
| CS725 | 13 | 13 |
| **TOTAL** | **45** | **45** |

### Documentary Verdicts

- VERIFIED: 44
- UNCERTAIN: 1
- UNSUPPORTED: 0
- Pending curriculum reviews: 0

**VERIFIED** refers to documentary support for the selected topic, not verified teaching delivery.

### Uncertain Curriculum Evidence

**CS632-T008 — Data cleaning (heading only)**

- Evidence scope: `reading_list_only`
- Evidence note: Official IIT Bombay CS632 Spring 2026 webpage: List of papers > Approximate Functional Dependencies and Data cleaning. The section heading mentions Data cleaning, but the listed papers primarily concern functional dependencies and relationship discovery. Human reviewer confirmed heading-level evidence without sufficient direct support for specific data-cleaning methods. Verdict: UNCERTAIN. Evidence scope: reading_list_only. No actual teaching delivery or curriculum coverage is inferred.

## 4. Industry Skill-Mapping Findings

Ten canonical industry skills were considered.

| Skill | Literal candidates | Source mention status |
|---|---:|---|
| airflow | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| aws | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| azure data factory | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| data pipelines | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| etl | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| gcp | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| pyspark | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| python | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| snowflake | 0 | NO_PROVISIONAL_LITERAL_CANDIDATE |
| sql | 2 | EXPLICIT_IN_OFFICIAL_READING_LIST |

### Reviewed SQL Candidates

| Topic | Matching fields | Mention verdict | Evidence scope |
|---|---|---|---|
| CS632-T009 | skill_concept_candidate | EXPLICIT_IN_OFFICIAL_READING_LIST | reading_list_only |
| CS632-T010 | topic_text; skill_concept_candidate | EXPLICIT_IN_OFFICIAL_READING_LIST | reading_list_only |

Both SQL candidates relate to the official CS632 Spring 2026 reading list.

CS632-T009 contains SQL in a researcher-assigned skill-concept field. The source reading list independently contains SQL in relevant paper titles.

CS632-T010 contains SQL in the curriculum topic text and researcher-assigned concept; the reading-list evidence also explicitly mentions SQL.

**These are reading-list mentions, not evidence that SQL programming was taught.**

For the other nine industry skills, the provisional literal-matching procedure identified no candidates in this selected dataset.

This does not establish that those skills are absent from IIT Bombay courses.

## 5. Curriculum Coverage and Gap Assessment

For all ten skills:

- Curriculum coverage status: `UNKNOWN`.
- Gap assessment status: `NOT_ASSESSABLE`.
- No curriculum coverage scores were assigned.
- No curriculum gap scores were assigned.

Literal mentions, paper titles, and researcher-derived concepts are insufficient to establish teaching coverage.

## 6. Independent Evaluation

A blank ten-skill reference-label template has been created.

Independent reviewer instructions have also been prepared.

Reference labels are pending independent review of the selected 45-record corpus.

Therefore:

- Precision: NOT AVAILABLE.
- Recall: NOT AVAILABLE.
- F1: NOT AVAILABLE.

No evaluation metric is reported without complete independent human reference labels.

The eventual benchmark will assess skill-level literal-mention detection only, not curriculum coverage.

## 7. Limitations

1. The dataset is a selected, nonrandom curriculum sample.
2. Reading-list inclusion does not prove classroom delivery.
3. Some concept fields contain researcher interpretations.
4. Literal candidate absence does not establish skill absence.
5. The ten-skill benchmark is small.
6. Independent evaluation labels are not yet available.
7. Skill coverage and curriculum gap conclusions remain unresolved.

## 8. Reproducibility Files

- `a07_human_validation.csv`
- `a07_skill_mapping_review.csv`
- `a07_ten_skill_summary.csv`
- `a07_independent_label_template.csv`
- `a07_independent_reviewer_instructions.md`

Original inputs include:

- `data/processed/curriculum_topics.csv`
- `data/reference/skill_aliases.csv`

## 9. Next Steps

1. Obtain independently reviewed reference labels.
2. Run evaluation only after verifying label independence.
3. Run A-07 integrity and reproducibility checks.
4. Submit a separate Draft PR for team review.

## 10. Conclusion

All 45 selected curriculum records received documentary human review: 44 VERIFIED and one UNCERTAIN.

Two SQL reading-list mention candidates were reviewed. The remaining nine skills had no provisional literal candidates.

No verified curriculum-coverage or skill-gap conclusion can be drawn from these results.

