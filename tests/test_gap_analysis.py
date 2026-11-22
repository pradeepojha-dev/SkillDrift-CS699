"""Tests for A-04's conservative provisional demand–evidence audit."""
import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.gap_analysis import SKILLS, build_audit, read_candidates, read_snapshot, write_audit


def make_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class GapAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.snapshot = self.folder / 'snapshot.csv'
        self.candidates = self.folder / 'candidates.csv'
        self.snapshot_rows = [
            {'Date': '2026-11-22', 'Skill': skill, 'Mumbai %': '20.0',
             'Pune %': '30.0', 'Bengaluru %': '10.0'} for skill in SKILLS
        ]
        self.candidate_rows = [
            {'curriculum_id': 'provisional', 'canonical_skill': 'sql',
             'course_id': 'CS632', 'topic_id': 'CS632-T009',
             'evidence_field': 'skill_concept_candidate',
             'source_url': 'https://example.edu/course', 'source_locator': 'Reading list',
             'evidence_scope': 'reading_list_only', 'coverage_status': 'unknown',
             'coverage_score': '', 'curriculum_review_status': 'unreviewed',
             'alias_reviewed_by': 'PENDING_HUMAN_REVIEW'},
            {'curriculum_id': 'provisional', 'canonical_skill': 'sql',
             'course_id': 'CS632', 'topic_id': 'CS632-T010',
             'evidence_field': 'topic_text',
             'source_url': 'https://example.edu/course', 'source_locator': 'Reading list',
             'evidence_scope': 'reading_list_only', 'coverage_status': 'unknown',
             'coverage_score': '', 'curriculum_review_status': 'unreviewed',
             'alias_reviewed_by': 'PENDING_HUMAN_REVIEW'},
        ]
        self._save()

    def _save(self):
        make_csv(self.snapshot, ['Date', 'Skill', 'Mumbai %', 'Pune %', 'Bengaluru %'], self.snapshot_rows)
        make_csv(self.candidates, ['curriculum_id', 'canonical_skill', 'course_id',
                                  'topic_id', 'evidence_field', 'source_url', 'source_locator',
                                  'evidence_scope', 'coverage_status', 'coverage_score',
                                  'curriculum_review_status', 'alias_reviewed_by'], self.candidate_rows)

    def test_ten_rows_with_literal_candidate_provenance(self):
        rows = build_audit(self.snapshot, self.candidates)
        self.assertEqual(10, len(rows))
        sql = next(r for r in rows if r['canonical_skill'] == 'sql')
        self.assertEqual('2', sql['literal_candidate_count'])
        self.assertEqual('1', sql['topic_text_candidate_count'])
        self.assertEqual('1', sql['researcher_concept_candidate_count'])
        self.assertEqual('CS632-T009;CS632-T010', sql['candidate_topic_ids'])
        self.assertEqual('reading_list_only', sql['candidate_evidence_scopes'])
        self.assertEqual('20.0', sql['Mumbai %'])
        self.assertEqual('2026-11-22', sql['snapshot_date'])

    def test_unknown_for_every_skill_even_with_no_candidate(self):
        rows = build_audit(self.snapshot, self.candidates)
        for r in rows:
            self.assertEqual('unknown', r['curriculum_coverage_status'])
            self.assertEqual('', r['curriculum_coverage_score'])
            self.assertEqual('NOT_ASSESSABLE', r['gap_assessment_status'])
            self.assertEqual('', r['gap_score'])
            self.assertEqual('true', r['human_review_required'])
        no_match = next(r for r in rows if r['canonical_skill'] == 'python')
        self.assertEqual('NO_LITERAL_CANDIDATE', no_match['evidence_status'])
        self.assertIn('does not establish', no_match['interpretation'])

    def test_rejects_non_unknown_coverage_without_reinterpreting(self):
        self.candidate_rows[0]['coverage_status'] = 'covered'
        self._save()
        with self.assertRaisesRegex(ValueError, 'UNKNOWN'):
            read_candidates(self.candidates)

    def test_rejects_invalid_snapshot_or_missing_skill(self):
        self.snapshot_rows[0]['Mumbai %'] = '101.0'
        self._save()
        with self.assertRaisesRegex(ValueError, 'out-of-range'):
            read_snapshot(self.snapshot)
        self.snapshot_rows.pop()
        self.snapshot_rows[0]['Mumbai %'] = '20.0'
        self._save()
        with self.assertRaisesRegex(ValueError, 'all 10'):
            read_snapshot(self.snapshot)

    def test_rejects_duplicates_and_historical(self):
        self.candidate_rows.append(dict(self.candidate_rows[0]))
        self._save()
        with self.assertRaisesRegex(ValueError, 'duplicate candidate'):
            read_candidates(self.candidates)
        self.candidate_rows.pop()
        self.candidate_rows[0]['course_id'] = 'CS317'
        self._save()
        with self.assertRaisesRegex(ValueError, 'historical'):
            read_candidates(self.candidates)

    def test_refuses_overwrite_of_generated_csv(self):
        dest = self.folder / 'result.csv'
        rows = build_audit(self.snapshot, self.candidates)
        write_audit(rows, dest)
        original = dest.read_bytes()
        with self.assertRaises(FileExistsError):
            write_audit(rows, dest)
        self.assertEqual(original, dest.read_bytes())


if __name__ == '__main__':
    unittest.main()
