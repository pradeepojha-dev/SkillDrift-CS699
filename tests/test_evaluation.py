"""A-05 evaluator tests use synthetic human labels, never real gold labels."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.gap_analysis import SKILLS, build_audit, write_audit
from evaluation.evaluate import (
    TEMPLATE_COLUMNS, check_provisional_inputs, evaluate_reviewed,
    main, make_review_template, write_review_template,
)


def save_csv(path, fieldnames, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.snapshot = self.folder / 'snapshot.csv'
        self.candidates = self.folder / 'candidates.csv'
        self.audit = self.folder / 'audit.csv'
        self.labels = self.folder / 'labels.csv'
        save_csv(self.snapshot, ['Date', 'Skill', 'Mumbai %', 'Pune %', 'Bengaluru %'], [
            {'Date': '2026-11-22', 'Skill': s, 'Mumbai %': '20',
             'Pune %': '30', 'Bengaluru %': '10'} for s in SKILLS
        ])
        self.candidate_rows = [
            {'curriculum_id': 'provisional', 'canonical_skill': 'sql',
             'course_id': 'CS632', 'topic_id': 'CS632-T009',
             'evidence_field': 'skill_concept_candidate',
             'source_url': 'https://example.edu', 'source_locator': 'Reading list',
             'evidence_scope': 'reading_list_only', 'coverage_status': 'unknown',
             'coverage_score': '', 'curriculum_review_status': 'unreviewed',
             'alias_reviewed_by': 'PENDING_HUMAN_REVIEW'},
            {'curriculum_id': 'provisional', 'canonical_skill': 'sql',
             'course_id': 'CS632', 'topic_id': 'CS632-T010',
             'evidence_field': 'topic_text',
             'source_url': 'https://example.edu', 'source_locator': 'Reading list',
             'evidence_scope': 'reading_list_only', 'coverage_status': 'unknown',
             'coverage_score': '', 'curriculum_review_status': 'unreviewed',
             'alias_reviewed_by': 'PENDING_HUMAN_REVIEW'},
        ]
        self._save_candidates()
        self.audit_rows = build_audit(self.snapshot, self.candidates)
        write_audit(self.audit_rows, self.audit)

    def _save_candidates(self):
        save_csv(self.candidates,
                 ['curriculum_id', 'canonical_skill', 'course_id', 'topic_id',
                  'evidence_field', 'source_url', 'source_locator',
                  'evidence_scope', 'coverage_status', 'coverage_score',
                  'curriculum_review_status', 'alias_reviewed_by'], self.candidate_rows)

    def _save_review_labels(self, positive_skills=('sql',)):
        save_csv(self.labels, TEMPLATE_COLUMNS, [
            {'canonical_skill': skill,
             'reference_label': 'present' if skill in positive_skills else 'absent',
             'reviewer': 'Synthetic Tester', 'review_date': '2026-11-23',
             'manual_evidence': 'Synthetic-only independent full corpus review',
             'review_notes': ''} for skill in SKILLS
        ])

    def test_blind_template_has_no_inferred_gold_labels(self):
        rows = make_review_template(self.audit, self.candidates)
        self.assertEqual(10, len(rows))
        self.assertEqual(list(SKILLS), [r['canonical_skill'] for r in rows])
        self.assertTrue(all(r['reference_label'] == '' and r['reviewer'] == '' for r in rows))
        self.assertEqual(set(TEMPLATE_COLUMNS), set(rows[0]))
        self.assertNotIn('literal_candidate_count', rows[0])

    def test_rejects_unreviewed_gold_template(self):
        write_review_template(make_review_template(self.audit, self.candidates), self.labels)
        with self.assertRaisesRegex(ValueError, 'Incomplete/invalid human reference'):
            evaluate_reviewed(self.audit, self.candidates, self.labels)

    def test_refuses_to_guess_metrics_when_one_label_missing(self):
        self._save_review_labels()
        with self.labels.open('r', newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        rows[0]['reference_label'] = ''
        save_csv(self.labels, TEMPLATE_COLUMNS, rows)
        with self.assertRaisesRegex(ValueError, 'Incomplete/invalid'):
            evaluate_reviewed(self.audit, self.candidates, self.labels)

    def test_synthetic_complete_labels_calculate_confusion_matrix(self):
        # Synthetic independent reference: SQL & Python present; only SQL predicted.
        self._save_review_labels(positive_skills=('sql', 'python'))
        report = evaluate_reviewed(self.audit, self.candidates, self.labels)
        self.assertEqual({'TP': 1, 'FP': 0, 'TN': 8, 'FN': 1}, report['confusion_matrix'])
        self.assertEqual({'precision': 1.0, 'recall': 0.5, 'f1': 0.6667,
                          'accuracy': 0.9}, report['metrics'])
        self.assertEqual('python', report['disagreements'][0]['canonical_skill'])
        self.assertEqual('FN', report['disagreements'][0]['error_type'])
        self.assertIn('NOT', ' '.join(report['limitations']))

    def test_synthetic_false_positive_and_false_negative(self):
        self._save_review_labels(positive_skills=('python',))
        report = evaluate_reviewed(self.audit, self.candidates, self.labels)
        self.assertEqual({'TP': 0, 'FP': 1, 'TN': 8, 'FN': 1}, report['confusion_matrix'])
        self.assertEqual(0, report['metrics']['f1'])
        self.assertEqual({'python', 'sql'}, {x['canonical_skill'] for x in report['disagreements']})

    def test_rejects_missing_reviewer_evidence_and_bad_date(self):
        self._save_review_labels()
        with self.labels.open('r', newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        rows[0]['manual_evidence'] = ''
        save_csv(self.labels, TEMPLATE_COLUMNS, rows)
        with self.assertRaisesRegex(ValueError, 'Missing reviewer'):
            evaluate_reviewed(self.audit, self.candidates, self.labels)
        rows[0]['manual_evidence'] = 'Synthetic review'
        rows[0]['review_date'] = 'Nov 23'
        save_csv(self.labels, TEMPLATE_COLUMNS, rows)
        with self.assertRaisesRegex(ValueError, 'Invalid ISO'):
            evaluate_reviewed(self.audit, self.candidates, self.labels)

    def test_detects_a03_a04_count_mismatch(self):
        self.audit_rows[1]['literal_candidate_count'] = '9'
        self.audit.unlink()
        write_audit(self.audit_rows, self.audit)
        with self.assertRaisesRegex(ValueError, 'count mismatch'):
            check_provisional_inputs(self.audit, self.candidates)

    def test_detects_claim_of_verified_coverage(self):
        self.audit_rows[1]['curriculum_coverage_status'] = 'covered'
        self.audit.unlink()
        write_audit(self.audit_rows, self.audit)
        with self.assertRaisesRegex(ValueError, 'Unexpected coverage'):
            check_provisional_inputs(self.audit, self.candidates)

    def test_cli_prepare_does_not_overwrite_and_score_requires_labels(self):
        path = self.folder / 'blind.csv'
        args = ['prepare', '--audit', str(self.audit), '--candidates', str(self.candidates),
                '--output', str(path)]
        self.assertEqual(0, main(args))
        original = path.read_bytes()
        self.assertEqual(1, main(args))
        self.assertEqual(original, path.read_bytes())
        report = self.folder / 'report.json'
        self.assertEqual(1, main(['score', '--audit', str(self.audit), '--candidates', str(self.candidates),
                                  '--labels', str(path), '--output', str(report)]))
        self.assertFalse(report.exists())

    def test_cli_score_uses_only_completed_synthetic_labels(self):
        self._save_review_labels()
        output = self.folder / 'result.json'
        self.assertEqual(0, main(['score', '--audit', str(self.audit), '--candidates', str(self.candidates),
                                  '--labels', str(self.labels), '--output', str(output)]))
        self.assertEqual(1, json.loads(output.read_text(encoding='utf-8'))['confusion_matrix']['TP'])


if __name__ == '__main__':
    unittest.main()
