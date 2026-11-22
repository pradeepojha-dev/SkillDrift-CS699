"""A-06 scientific-integrity regression tests: synthetic fixtures, NOT gold labels."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.gap_analysis import SKILLS, OUTPUT_COLUMNS, build_audit, write_audit
from evaluation.evaluate import check_provisional_inputs
from nlp.match_curriculum import COLUMNS, find_candidates, literal_phrase_present, write_candidates
from validation.scientific_checks import (
    check_candidate_provenance, main, run_checks, write_report,
)


CURRICULUM_FIELDS = [
    'curriculum_id', 'course_id', 'topic_id', 'topic_text',
    'skill_concept_candidate', 'source_verification_status',
    'review_status', 'analysis_group', 'source_url', 'source_locator',
    'source_page', 'evidence_scope',
]
ALIAS_FIELDS = ['alias', 'canonical_skill', 'category', 'reviewed_by', 'notes']
SNAPSHOT_FIELDS = ['Date', 'Skill', 'Mumbai %', 'Pune %', 'Bengaluru %']


def write_csv(path, columns, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


class ScientificValidationTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.curriculum = self.root / 'curriculum.csv'
        self.aliases = self.root / 'aliases.csv'
        self.snapshot = self.root / 'snapshot.csv'
        self.rows = [
            self.topic('CS632', 'CS632-T009', 'Query verification', 'SQL query verification'),
            self.topic('CS632', 'CS632-T010', 'Text-to-SQL evaluation', 'Text-to-SQL'),
            self.topic('CS631', 'CS631-T005', 'NoSQL indexing', 'NoSQL systems'),
            self.topic('CS317', 'CS317-T001', 'SQL', 'SQL', group='HISTORICAL_2008'),
            self.topic('CS725', 'CS725-T001', 'PySpark requirements', 'PySpark', status='UNSUPPORTED'),
        ]
        write_csv(self.curriculum, CURRICULUM_FIELDS, self.rows)
        self.alias_rows = [dict(alias=skill, canonical_skill=skill,
                                category='test', reviewed_by='PENDING_HUMAN_REVIEW', notes='')
                           for skill in SKILLS]
        self.alias_rows.append(dict(alias='structured query language', canonical_skill='sql',
                                    category='test', reviewed_by='PENDING_HUMAN_REVIEW', notes=''))
        write_csv(self.aliases, ALIAS_FIELDS, self.alias_rows)
        self.snapshot_rows = [dict(Date='2026-11-22', Skill=skill, **{
            'Mumbai %': '40.0', 'Pune %': '20.0', 'Bengaluru %': '10.0',
        }) for skill in SKILLS]
        write_csv(self.snapshot, SNAPSHOT_FIELDS, self.snapshot_rows)

    @staticmethod
    def topic(course, topic, text, concept, *, group='PRIMARY_2025_2026', status='VERIFIED'):
        return dict(curriculum_id='synthetic-provisional', course_id=course,
                    topic_id=topic, topic_text=text, skill_concept_candidate=concept,
                    source_verification_status=status, review_status='unreviewed',
                    analysis_group=group, source_url='https://example.edu/synthetic-course',
                    source_locator=f'Synthetic reference {topic}', source_page='',
                    evidence_scope='reading_list_only')

    def test_end_to_end_provenance_replay_and_no_gold_metrics(self):
        report = run_checks(self.curriculum, self.aliases, self.snapshot)
        self.assertEqual('PROVISIONAL_PIPELINE_CHECKS_PASSED', report['validation_status'])
        self.assertEqual(10, report['canonical_skill_count'])
        self.assertEqual(10, report['audit_row_count'])
        self.assertEqual(2, report['literal_candidate_count'])
        self.assertEqual(1, report['candidate_topic_text_count'])
        self.assertEqual(1, report['candidate_researcher_concept_count'])
        self.assertFalse(report['real_evaluation_metrics_available'])
        self.assertTrue(all(report['checks'].values()))
        self.assertNotIn('precision', report)
        self.assertNotIn('f1', report)
        self.assertEqual(64, len(report['sha256_of_inputs']['snapshot']))

    def test_repeat_run_has_identical_hashes(self):
        first = run_checks(self.curriculum, self.aliases, self.snapshot)
        second = run_checks(self.curriculum, self.aliases, self.snapshot)
        self.assertEqual(first, second)

    def test_whole_phrase_boundaries_not_nosql(self):
        self.assertTrue(literal_phrase_present('sql', 'Text-to-SQL evaluation'))
        self.assertFalse(literal_phrase_present('sql', 'NoSQL systems'))
        self.assertEqual({'sql'}, {r['canonical_skill'] for r in find_candidates(self.curriculum, self.aliases)})

    def test_reject_source_url_tampering(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['source_url'] = 'https://example.edu/incorrect'
        with self.assertRaisesRegex(ValueError, 'source provenance mismatch'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_forged_match_phrase(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['matched_phrase'] = 'structured query language'
        with self.assertRaisesRegex(ValueError, 'not present'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_inconsistent_match_method(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['match_method'] = 'fuzzy'
        with self.assertRaisesRegex(ValueError, 'match_method'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_unapproved_coverage(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['coverage_status'] = 'covered'
        with self.assertRaisesRegex(ValueError, 'Unapproved curriculum coverage'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_nonprimary_candidate(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['course_id'] = 'CS317'
        candidates[0]['topic_id'] = 'CS317-T001'
        with self.assertRaisesRegex(ValueError, 'supported primary'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_unsupported_candidate(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidates[0]['course_id'] = 'CS725'
        candidates[0]['topic_id'] = 'CS725-T001'
        with self.assertRaisesRegex(ValueError, 'supported primary'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates)

    def test_reject_duplicate_candidates(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        with self.assertRaisesRegex(ValueError, 'Duplicate A-03 candidate'):
            check_candidate_provenance(self.curriculum, self.aliases, candidates + [dict(candidates[0])])

    def test_a05_detects_forged_a04_gap_score(self):
        candidates = find_candidates(self.curriculum, self.aliases)
        candidate_csv = self.root / 'candidates.csv'
        audit_csv = self.root / 'audit.csv'
        write_candidates(candidates, candidate_csv)
        audit = build_audit(self.snapshot, candidate_csv)
        audit[0]['gap_score'] = '100'
        write_audit(audit, audit_csv)
        with self.assertRaisesRegex(ValueError, 'coverage, gap score'):
            check_provisional_inputs(audit_csv, candidate_csv)

    def test_reject_bad_demand_snapshot(self):
        self.snapshot_rows[0]['Pune %'] = '120'
        write_csv(self.snapshot, SNAPSHOT_FIELDS, self.snapshot_rows)
        with self.assertRaisesRegex(ValueError, 'out-of-range'):
            run_checks(self.curriculum, self.aliases, self.snapshot)

    def test_write_report_never_overwrites(self):
        output = self.root / 'validation.json'
        report = run_checks(self.curriculum, self.aliases, self.snapshot)
        write_report(report, output, (self.curriculum, self.aliases, self.snapshot))
        original = output.read_bytes()
        with self.assertRaises(FileExistsError):
            write_report(report, output)
        self.assertEqual(original, output.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Output must differ'):
            write_report(report, self.curriculum, (self.curriculum,))

    def test_cli_success_and_existing_output_rejected(self):
        output = self.root / 'a06_report.json'
        args = ['--curriculum', str(self.curriculum), '--aliases', str(self.aliases),
                '--snapshot', str(self.snapshot), '--output', str(output)]
        self.assertEqual(0, main(args))
        data = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual('PROVISIONAL_PIPELINE_CHECKS_PASSED', data['validation_status'])
        self.assertEqual(1, main(args))


if __name__ == '__main__':
    unittest.main()
