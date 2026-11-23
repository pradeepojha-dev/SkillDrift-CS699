"""A-07 integrity checks. Run from any directory; no third-party packages."""

import csv
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEWS = ROOT / "curriculum/reviews"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


class TestA07Integrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.original_fields, cls.original = read_csv(
            ROOT / "data/processed/curriculum_topics.csv"
        )
        cls.human_fields, cls.human = read_csv(
            REVIEWS / "a07_human_validation.csv"
        )
        _, cls.mappings = read_csv(
            REVIEWS / "a07_skill_mapping_review.csv"
        )
        _, cls.summary = read_csv(
            REVIEWS / "a07_ten_skill_summary.csv"
        )
        _, cls.aliases = read_csv(
            ROOT / "data/reference/skill_aliases.csv"
        )
        _, cls.labels = read_csv(
            REVIEWS / "a07_independent_label_template.csv"
        )

    def test_01_original_datasets_unchanged(self):
        result = subprocess.run(
            [
                "git", "diff", "--quiet", "HEAD", "--",
                "data/processed/curriculum_topics.csv",
                "data/reference/skill_aliases.csv",
            ],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0,
            "Original tracked datasets differ from HEAD."
        )

    def test_02_all_original_records_preserved(self):
        self.assertEqual(len(self.original), 45)
        self.assertEqual(len(self.human), 45)

        self.assertTrue(
            set(self.original_fields).issubset(self.human_fields)
        )

        original_by_id = {
            r["topic_id"]: r for r in self.original
        }
        human_by_id = {
            r["topic_id"]: r for r in self.human
        }

        self.assertEqual(len(original_by_id), 45)
        self.assertEqual(len(human_by_id), 45)
        self.assertEqual(set(original_by_id), set(human_by_id))

        for topic_id, original in original_by_id.items():
            reviewed = human_by_id[topic_id]

            for field in self.original_fields:
                self.assertEqual(
                    original[field],
                    reviewed[field],
                    f"{topic_id}: original field changed: {field}"
                )

    def test_03_curriculum_review_verdicts(self):
        self.assertTrue(all(
            r["a07_human_review_status"] == "CONFIRMED"
            for r in self.human
        ))

        verdicts = Counter(
            r["a07_source_verdict"] for r in self.human
        )

        self.assertEqual(
            verdicts,
            {"VERIFIED": 44, "UNCERTAIN": 1}
        )

        uncertain = [
            r["topic_id"] for r in self.human
            if r["a07_source_verdict"] == "UNCERTAIN"
        ]
        self.assertEqual(uncertain, ["CS632-T008"])

        expected = {
            "CS215": 10,
            "CS631": 12,
            "CS632": 10,
            "CS725": 13,
        }

        counts = Counter(r["course_id"] for r in self.human)
        self.assertEqual(dict(counts), expected)

    def test_04_sql_mapping_provenance(self):
        self.assertEqual(len(self.mappings), 2)

        by_id = {r["topic_id"]: r for r in self.human}

        expected_fields = {
            "CS632-T009": {"skill_concept_candidate"},
            "CS632-T010": {
                "topic_text",
                "skill_concept_candidate",
            },
        }

        self.assertEqual(
            {r["topic_id"] for r in self.mappings},
            set(expected_fields)
        )

        sql_pattern = re.compile(
            r"(?<![A-Za-z0-9])sql(?![A-Za-z0-9])",
            re.IGNORECASE
        )

        for mapping in self.mappings:
            topic_id = mapping["topic_id"]
            original = by_id[topic_id]

            self.assertEqual(mapping["canonical_skill"], "sql")
            self.assertEqual(
                mapping["a07_mapping_review_status"], "CONFIRMED"
            )
            self.assertEqual(
                mapping["a07_skill_mention_verdict"],
                "EXPLICIT_IN_OFFICIAL_READING_LIST"
            )
            self.assertEqual(
                mapping["curriculum_coverage_status"], "UNKNOWN"
            )
            self.assertEqual(
                mapping["evidence_scope"], "reading_list_only"
            )

            self.assertEqual(
                mapping["topic_text"], original["topic_text"]
            )
            self.assertEqual(
                mapping["researcher_skill_concept"],
                original["skill_concept_candidate"]
            )
            self.assertEqual(
                mapping["source_url"], original["source_url"]
            )
            self.assertEqual(
                mapping["source_locator"], original["source_locator"]
            )

            actual_fields = {
                field
                for field in (
                    "topic_text",
                    "skill_concept_candidate",
                )
                if sql_pattern.search(original[field])
            }

            recorded_fields = {
                field.strip()
                for field in mapping["matched_fields"].split(";")
            }

            self.assertEqual(
                actual_fields, expected_fields[topic_id]
            )
            self.assertEqual(
                recorded_fields, actual_fields
            )

    def test_05_ten_skill_summary(self):
        self.assertEqual(len(self.aliases), 26)
        self.assertEqual(len(self.summary), 10)

        skills = {
            r["canonical_skill"] for r in self.aliases
        }
        self.assertEqual(len(skills), 10)

        summary_by_skill = {
            r["canonical_skill"]: r for r in self.summary
        }
        self.assertEqual(set(summary_by_skill), skills)

        for skill, row in summary_by_skill.items():
            expected_count = 2 if skill == "sql" else 0

            self.assertEqual(
                int(row["candidate_count"]), expected_count
            )
            self.assertEqual(
                row["curriculum_coverage_status"], "UNKNOWN"
            )
            self.assertEqual(
                row["gap_assessment_status"], "NOT_ASSESSABLE"
            )

            if skill == "sql":
                self.assertEqual(
                    set(row["matched_topic_ids"].split("; ")),
                    {"CS632-T009", "CS632-T010"}
                )
                self.assertEqual(
                    row["source_mention_status"],
                    "EXPLICIT_IN_OFFICIAL_READING_LIST"
                )
            else:
                self.assertFalse(row["matched_topic_ids"].strip())
                self.assertEqual(
                    row["source_mention_status"],
                    "NO_PROVISIONAL_LITERAL_CANDIDATE"
                )

    def test_06_independent_labels_remain_blank(self):
        self.assertEqual(len(self.labels), 10)

        skills = {
            r["canonical_skill"] for r in self.aliases
        }

        self.assertEqual(
            {r["canonical_skill"] for r in self.labels},
            skills
        )

        for row in self.labels:
            for field in (
                "reference_label",
                "reviewer",
                "review_date",
                "manual_evidence",
                "review_notes",
            ):
                self.assertFalse(
                    row[field].strip(),
                    f"Reference labels not blank: {field}"
                )

    def test_07_research_documentation_exists(self):
        files = [
            REVIEWS / "a07_research_findings.md",
            REVIEWS / "a07_independent_reviewer_instructions.md",
        ]

        for path in files:
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 100)

        report = files[0].read_text(encoding="utf-8")

        self.assertIn("45", report)
        self.assertIn("NOT_ASSESSABLE", report)
        self.assertIn("UNKNOWN", report)
        self.assertIn("NOT AVAILABLE", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
