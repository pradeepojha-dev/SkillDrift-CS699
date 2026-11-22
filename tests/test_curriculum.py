"""A-01 checks for data integrity. Does NOT certify source review by a human."""
from collections import Counter
import csv
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    with (ROOT/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

class CurriculumQualityTests(unittest.TestCase):
    def test_original_56_rows_all_accounted_for(self):
        a=load('curriculum/reviews/candidate_row_verification.csv')
        self.assertEqual(len(a),56)
        self.assertEqual([int(x['candidate_row']) for x in a],list(range(1,57)))
        self.assertEqual(Counter(x['verdict'] for x in a),{'VERIFIED':54,'UNCERTAIN':1,'UNSUPPORTED':1})

    def test_primary_and_historical_separate(self):
        p=load('data/processed/curriculum_topics.csv')
        h=load('data/processed/curriculum_topics_historical_cs317.csv')
        self.assertEqual(len(p),45)
        self.assertEqual(len(h),10)
        self.assertFalse(any(x['course_id']=='CS317' for x in p))
        self.assertEqual({x['course_id'] for x in h},{'CS317'})
        self.assertTrue(all(x['source_page']=='14' for x in h))
        self.assertTrue(all(x['source_page']=='' for x in p))

    def test_unsupported_excluded_and_not_human_approved(self):
        p=load('data/processed/curriculum_topics.csv')
        self.assertFalse(any(x['source_candidate_row']=='33' for x in p))
        self.assertTrue(all(x['review_status']=='unreviewed' for x in p))
        self.assertTrue(all(x['source_url'].startswith('https://www.cse.iitb.ac.in/') for x in p))
        self.assertEqual(sum(x['source_verification_status']=='UNCERTAIN' for x in p),1)

if __name__=='__main__':
    unittest.main()
