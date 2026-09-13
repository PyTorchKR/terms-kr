import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('usage', Path(__file__).resolve().parents[1] / 'scripts/usage-statistics/update_usage_counts.py')
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)


def candidates(*values):
    return {'gradient': {'variants': list(values), 'unsupportedVariants': [], 'origin': 'hf-collected'}}


def doc(sha='first', eligible=True):
    return {'source': 'transformers', 'path': 'docs/source/ko/test.md', 'blobSha': sha, 'eligible': eligible, 'reason': 'paired-translation' if eligible else 'english-missing'}


class UsageTests(unittest.TestCase):
    def counts(self, text, values=('기울기',)):
        return usage.count_document(text, usage.compile_patterns(candidates(*values)))[0]

    def test_prose_only(self):
        text = '---\ntitle: 기울기\n---\n# 기울기\n\n기울기를 [기울기](https://example.com/기울기)\n\n`기울기`\n\n```python\n기울기\n```\n\n    기울기\n\n<!-- 기울기 -->\n\n![기울기](image.png)\n\n<div>기울기</div>\n'
        self.assertEqual(self.counts(text), {'gradient': {'기울기': 3}})

    def test_table_lists_quotes(self):
        self.assertEqual(self.counts('| 이름 | 값 |\n| --- | --- |\n| 기울기 | 기울기 |\n\n- 기울기\n\n> 기울기'), {'gradient': {'기울기': 4}})

    def test_longest_nonoverlap_within_term(self):
        self.assertEqual(self.counts('평가지표 지표 평가지표', ('지표', '평가지표')), {'gradient': {'평가지표': 2, '지표': 1}})

    def test_normalization_particles_and_no_word_boundary(self):
        self.assertEqual(self.counts('그래디언트의 경사하강법 경사', ('그래디언트', '경사')), {'gradient': {'그래디언트': 1, '경사': 2}})

    def test_spaces_case_unicode(self):
        self.assertEqual(self.counts('KV   캐시 KV 캐시', ('kv 캐시',)), {'gradient': {'kv 캐시': 2}})
        self.assertEqual(self.counts('기울기'), {'gradient': {'기울기': 1}})
        self.assertEqual(self.counts('평가 지표', ('평가지표',)), {})

    def test_no_cross_block_or_code_or_cell_matching(self):
        self.assertEqual(self.counts('기울\n\n기\n\n기울`ignored`기\n\n| 기울 | 기 |\n| --- | --- |\n', ('기울 기', '기울기')), {})

    def test_different_terms_independent(self):
        patterns = usage.compile_patterns({'short': {'variants': ['지표']}, 'long': {'variants': ['평가지표']}})
        self.assertEqual(usage.count_document('평가지표', patterns)[0], {'short': {'지표': 1}, 'long': {'평가지표': 1}})

    def update(self, docs, previous=None, compatible=True, texts=None):
        return usage.update_records(docs, previous or {}, compatible, lambda pending: {k: (texts or {}).get(k, '기울기') for k in pending}, candidates('기울기'), '2026-09-13T00:00:00Z')

    def test_add_noop_update_delete(self):
        first, stats = self.update({'a': doc()})
        self.assertEqual(stats['recounted'], 1)
        same, stats = self.update({'a': doc()}, first)
        self.assertEqual(same, first)
        self.assertEqual(stats['reused'], 1)
        changed, stats = self.update({'a': doc('second')}, first, texts={'a': '기울기 기울기'})
        self.assertEqual(changed['a']['counts']['gradient']['기울기'], 2)
        deleted, stats = self.update({}, changed)
        self.assertEqual(deleted, {})
        self.assertEqual(stats['deleted'], 1)

    def test_rename_exclude_reinclude(self):
        first, _ = self.update({'a': doc()})
        moved, stats = self.update({'b': doc()}, first)
        self.assertEqual(moved['b']['counts'], first['a']['counts'])
        self.assertEqual(stats['deleted'], 1)
        excluded, _ = self.update({'a': doc(eligible=False)}, first)
        self.assertEqual(excluded['a']['counts'], {})
        included, stats = self.update({'a': doc()}, excluded)
        self.assertEqual(stats['recounted'], 1)
        self.assertEqual(included['a']['counts'], first['a']['counts'])

    def test_rule_candidate_change_forces_recount(self):
        first, _ = self.update({'a': doc()})
        _, stats = self.update({'a': doc()}, first, compatible=False)
        self.assertEqual(stats['recounted'], 1)

    def test_missing_text_is_failure_not_zero(self):
        with self.assertRaises(KeyError):
            usage.update_records({'a': doc()}, {}, True, lambda _: {}, candidates('기울기'), 'now')

    def test_evidence_preserves_line_numbers(self):
        _, evidence = usage.count_document('---\ntitle: hi\n---\n\n# 제목\n\n기울기\n', usage.compile_patterns(candidates('기울기')))
        self.assertEqual(evidence['gradient']['기울기']['line'], 7)


if __name__ == '__main__':
    unittest.main()
