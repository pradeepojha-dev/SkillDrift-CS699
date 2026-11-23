# A-07 Independent Skill-Mention Evaluation

## Purpose

Independently establish reference labels for evaluating A-03
literal skill-mention detection.

This evaluation does NOT establish:
- Whether a skill was taught in a course.
- Whether students gained proficiency.
- Whether a curriculum skill gap exists.

## Files for Independent Reviewer

Corpus:
`data/processed/curriculum_topics.csv`

Blank label template:
`curriculum/reviews/a07_independent_label_template.csv`

The selected corpus contains 45 curriculum records.

## Evaluation Unit

One canonical industry skill.

There are 10 skills.

The reviewer assigns ONE reference label per skill
after examining ALL 45 selected curriculum records.

## Fields to Examine

1. `topic_id`
2. `course_id`
3. `topic_text`
4. `skill_concept_candidate`
5. `source_url`
6. `source_locator`
7. `evidence_scope`

The `skill_concept_candidate` field contains
researcher-assigned concepts and must not be confused
with exact official source wording.

## Label Definitions

### present

At least one relevant literal mention of the canonical
skill, or a manually validated equivalent expression,
appears in `topic_text` or `skill_concept_candidate`.

The reviewer must independently confirm that the
expression refers to the intended technical skill.

### absent

No relevant literal mention is found after independently
reviewing the entire selected 45-record corpus.

This means 'no literal mention in this dataset',
NOT 'the skill is absent from IIT Bombay courses'.

## Review Procedure

1. Open the original 45-record curriculum CSV.
2. Select one canonical industry skill.
3. Examine all 45 topic records for that skill.
4. Review possible aliases manually; proposed aliases
   are not automatically accepted as ground truth.
5. Inspect both `topic_text` and
   `skill_concept_candidate`.
6. Distinguish official wording from researcher-derived
   descriptions.
7. Where available, inspect the linked official source.
8. Assign `present` or `absent`.
9. Fill in `reviewer` and actual `review_date` (YYYY-MM-DD).
10. Record supporting evidence in `manual_evidence`.
11. Record uncertainty or limitations in `review_notes`.
12. Repeat until all 10 skills have been reviewed.

## Required Evidence

For a `present` label, record:
- Topic ID
- Matching field
- Exact matching expression
- Why the expression refers to the canonical skill
- Whether the expression is original or researcher-derived

For an `absent` label, record:
- That all 45 records were examined
- Both fields were considered
- That no qualifying literal mention was found

## Blinding Requirements

Before submitting reference labels, do NOT inspect:

- A-03 candidate predictions
- A-04 gap-audit predictions
- A-07 skill mapping review results
- A-07 ten-skill verification summary
- Model-generated precision, recall or F1 scores

These files could bias the reference labels.

## Required Output

Fill the existing template:

`curriculum/reviews/a07_independent_label_template.csv`

Columns:

- canonical_skill
- reference_label
- reviewer
- review_date
- manual_evidence
- review_notes

Do not change the column names or canonical skill names.

## Evaluation Limitations

- Only 10 canonical skills are evaluated.
- Only 45 selected curriculum records are considered.
- This is a small, selected benchmark.
- Literal mention detection is not course coverage.
- Reading-list evidence does not prove teaching delivery.
- Researcher-derived concepts are not independent
  confirmation of official course wording.
- No skill-gap claims can be made from these labels.

## Submission

Return the fully completed CSV to the A-07 owner.

Precision, recall and F1 may be calculated only after
all 10 independently reviewed reference labels are present.
