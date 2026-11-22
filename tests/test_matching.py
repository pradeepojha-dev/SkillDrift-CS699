"""A-03 provisional literal-candidate tests; no implied curriculum coverage."""
import csv
import tempfile
import unittest
from pathlib import Path

from nlp.match_curriculum import find_candidates, literal_phrase_present, write_candidates


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.aliases = self.root / 'aliases.csv'
        self.topics = self.root / 'topics.csv'
        with self.aliases.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['alias', 'canonical_skill', 'category', 'reviewed_by', 'notes'])
            writer.writerow(['sql', 'sql', 'database', 'PENDING_HUMAN_REVIEW', ''])
            writer.writerow(['structured query language', 'sql', 'database', 'PENDING_HUMAN_REVIEW', ''])
            writer.writerow(['python', 'python', 'programming', 'PENDING_HUMAN_REVIEW', ''])
        fields = [
            'curriculum_id', 'course_id', 'topic_id', 'topic_text',
            'skill_concept_candidate', 'source_verification_status',
            'review_status', 'analysis_group', 'source_url', 'source_locator',
            'source_page', 'evidence_scope',
        ]
        fixtures = [
            ('CS632-T009', 'Query equivalence and verification', 'SQL query verification', 'VERIFIED', 'PRIMARY_2025_2026'),
            ('CS632-T010', 'Text-to-SQL evaluation', 'Text-to-SQL', 'VERIFIED', 'PRIMARY_2025_2026'),
            ('CS631-T009', 'Big data systems', 'Big-data systems', 'VERIFIED', 'PRIMARY_2025_2026'),
            ('CS317-T001', 'SQL', 'SQL', 'VERIFIED', 'HISTORICAL_2008'),
            ('CS725-T001', 'Python assignments', 'Python', 'UNSUPPORTED', 'PRIMARY_2025_2026'),
        ]
        with self.topics.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for topic_id, title, candidate, status, group in fixtures:
                writer.writerow(dict(curriculum_id='provisional-v0', course_id=topic_id[:5],
                                    topic_id=topic_id, topic_text=title,
                                    skill_concept_candidate=candidate,
                                    source_verification_status=status, review_status='unreviewed',
                                    analysis_group=group, source_url='https://example.org/course',
                                    source_locator='research page', source_page='',
                                    evidence_scope='reading_list_only'))

    def test_whole_phrase_no_substring_guessing(self):
        self.assertTrue(literal_phrase_present('sql', 'Text-to-SQL evaluation'))
        self.assertFalse(literal_phrase_present('sql', 'NoSQL'))
        self.assertFalse(literal_phrase_present('pyspark', 'Big data systems'))

    def test_separates_derived_text_from_topic_text(self):
        result = find_candidates(self.topics, self.aliases)
        self.assertEqual([r['topic_id'] for r in result], ['CS632-T009', 'CS632-T010'])
        self.assertEqual([r['evidence_field'] for r in result],
                         ['skill_concept_candidate', 'topic_text'])
        self.assertTrue(all(r['coverage_status'] == 'unknown' for r in result))
        self.assertTrue(all(r['coverage_score'] == '' for r in result))
        self.assertTrue(all(r['alias_reviewed_by'] == 'PENDING_HUMAN_REVIEW' for r in result))

    def test_excludes_historical_and_unsupported(self):
        result = find_candidates(self.topics, self.aliases)
        self.assertFalse(any(r['course_id'] in {'CS317', 'CS725'} for r in result))

    def test_refuses_to_overwrite_output(self):
        path = self.root / 'candidates.csv'
        write_candidates(find_candidates(self.topics, self.aliases), path)
        with self.assertRaises(FileExistsError):
            write_candidates([], path)
        with path.open(newline='', encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)


if __name__ == '__main__':
    unittest.main()
