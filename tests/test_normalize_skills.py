"""Safety checks for provisional A-02 tag normalization (stdlib only)."""
from pathlib import Path
import csv
import tempfile
import unittest

from nlp.normalize_skills import load_aliases, lookup_key, normalize_skill_tags, normalize_tag, audit_input_csv

ROOT = Path(__file__).resolve().parents[1]


class NormalizeSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aliases = load_aliases(ROOT/'data/reference/skill_aliases.csv')

    def test_exact_and_casefold_and_alias(self):
        result = normalize_skill_tags(' PYTHON , Apache Airflow, Google Cloud Platform', self.aliases)
        self.assertEqual([r.canonical_skill for r in result], ['python','airflow','gcp'])
        self.assertEqual([r.match_method for r in result], ['exact','alias','alias'])

    def test_unknown_stays_unknown(self):
        for tag in ('spark','data warehousing','postgresql','azure','adf', 'sql optimization'):
            self.assertIsNone(normalize_tag(tag,self.aliases).canonical_skill, tag)

    def test_original_raw_tag_and_repeated_tags_preserved(self):
        results = normalize_skill_tags('SQL, sql ,Unlisted Tool',self.aliases)
        self.assertEqual([r.raw_tag for r in results],['SQL','sql','Unlisted Tool'])
        self.assertEqual([r.matched for r in results],[True,True,False])

    def test_conflicting_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'aliases.csv'
            path.write_text('alias,canonical_skill,category,reviewed_by,notes\nX,python,,,,\nx,sql,,,,\n',encoding='utf-8')
            with self.assertRaises(ValueError):
                load_aliases(path)

    def test_csv_audit_preserves_input_and_unmatched(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=Path(tmp)/'raw.csv'; audit=Path(tmp)/'out.csv'
            raw.write_text('skills,title\n"SQL, Spark",Role\n',encoding='utf-8')
            original=raw.read_bytes()
            result=audit_input_csv(raw,audit,self.aliases)
            self.assertEqual(result,2)
            self.assertEqual(original,raw.read_bytes())
            with audit.open(newline='') as f: rows=list(csv.DictReader(f))
            self.assertEqual(rows[0]['canonical_skill'],'sql')
            self.assertEqual(rows[1]['matched'],'false')
            with self.assertRaises(FileExistsError):
                audit_input_csv(raw,audit,self.aliases)

    def test_lookup_key_does_not_imply_synonyms(self):
        self.assertEqual(lookup_key('  PYSPARK\t  '),'pyspark')
        self.assertNotEqual(lookup_key('apache spark'),lookup_key('pyspark'))


if __name__=='__main__':
    unittest.main()
