"""Small local Git fixtures: no network, no real community repositories required."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('usage_sources', Path(__file__).resolve().parents[1] / 'scripts/usage-statistics/update_usage_counts.py')
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'site'
        self.sources = Path(self.temp.name) / 'sources'
        self.write_json('data/index.json', ['g.json'])
        self.write_json('data/g.json', [{'term': 'gradient', 'meanings': [{'korean': '기울기', 'definition': 'fixture', 'synonyms': []}]}])
        self.write_json('usage/variants.json', {'schemaVersion': 1, 'showWhenUnmatched': [], 'extraVariants': {}})
        self.config = {'schemaVersion': 1, 'sources': []}
        for sid in ('community-a', 'community-b'):
            repo = self.sources / sid
            repo.mkdir(parents=True)
            self.git(repo, 'init', '-q')
            for folder in ('ko', 'en'):
                (repo / folder).mkdir()
                (repo / folder / 'a.md').write_text('기울기 기울기' if folder == 'ko' else 'gradient', encoding='utf8')
            revision = self.commit(repo)
            self.config['sources'].append({
                'id': sid, 'label': sid, 'community': sid, 'repository': f'https://github.com/example/{sid}',
                'checkout': sid, 'ref': revision, 'root': 'ko', 'adapter': 'paired-markdown', 'exclude': [],
                'original': {'repository': f'https://github.com/example/{sid}', 'checkout': sid, 'ref': revision, 'root': 'en'},
            })
        self.save_config()

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf8')

    def git(self, repo, *args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, repo):
        self.git(repo, 'add', '.')
        self.git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.com', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        return self.git(repo, 'rev-parse', 'HEAD')

    def save_config(self):
        self.write_json('usage/sources.json', self.config)

    def run_update(self, **kwargs):
        return usage.run(self.root, self.sources, **kwargs)

    def summary(self):
        return usage.read_json(self.root / 'public/usage/term-usage.json')

    def outputs(self):
        return {p.relative_to(self.root): p.read_bytes() for folder in ('usage/state', 'public/usage') for p in (self.root / folder).glob('*')}

    def move_ref(self, index=0):
        source = self.config['sources'][index]
        revision = self.commit(self.sources / source['checkout'])
        source['ref'] = source['original']['ref'] = revision
        self.save_config()

    def test_missing_state_is_not_zero_and_arbitrary_source_is_supported(self):
        self.run_update(selected=['community-a'])
        result = self.summary()
        self.assertEqual(result['sources']['community-b']['status'], 'not-collected')
        self.assertIsNone(result['terms']['gradient']['bySource']['community-b']['occurrences'])
        self.assertEqual(result['terms']['gradient']['occurrences'], 2)

    def test_partial_update_needs_no_other_checkout_and_preserves_state(self):
        self.run_update()
        other = self.root / 'usage/state/community-b.json'
        before = other.read_bytes()
        (self.sources / 'community-b').rename(self.sources / 'unavailable')
        repo = self.sources / 'community-a'
        (repo / 'ko/a.md').write_text('기울기', encoding='utf8')
        self.move_ref()
        self.run_update(selected=['community-a'])
        self.assertEqual(other.read_bytes(), before)
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 3)
        self.assertEqual(self.run_update(selected=['community-a'])['filesChanged'], 0)
        self.assertEqual(self.run_update(selected=['community-a'], check_full=True)['fullCheck'], 'passed')

    def test_add_change_delete_and_revision_preserves_unchanged_counts(self):
        self.run_update()
        repo = self.sources / 'community-a'
        for folder in ('ko', 'en'):
            (repo / folder / 'new.md').write_text('기울기', encoding='utf8')
        self.move_ref()
        metrics = self.run_update(selected=['community-a'])['sources']['community-a']
        self.assertEqual(metrics['reused'], 1)
        self.assertEqual(metrics['recounted'], 1)
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 5)
        (repo / 'ko/new.md').unlink()
        self.move_ref()
        metrics = self.run_update(selected=['community-a'])['sources']['community-a']
        self.assertEqual(metrics['deleted'], 1)
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 4)

    def test_candidate_change_requires_other_sources_before_writing(self):
        self.run_update()
        before = self.outputs()
        self.write_json('usage/variants.json', {'schemaVersion': 1, 'showWhenUnmatched': [], 'extraVariants': {'gradient': ['경사']}})
        with self.assertRaisesRegex(ValueError, 'Stale snapshot'):
            self.run_update(selected=['community-a'])
        self.assertEqual(self.outputs(), before)
        self.run_update()
        self.assertEqual(len(self.summary()['terms']['gradient']['variants']), 2)

    def test_failures_leave_previous_outputs_untouched(self):
        self.run_update()
        before = self.outputs()
        (self.sources / 'community-b').rename(self.sources / 'unavailable')
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_update()
        self.assertEqual(self.outputs(), before)
        self.assertEqual(self.run_update(aggregate_only=True)['filesChanged'], 0)

    def test_wrong_root_unsupported_format_and_unknown_source_fail(self):
        self.run_update()
        before = self.outputs()
        with self.assertRaisesRegex(ValueError, 'Unknown source'):
            self.run_update(selected=['typo'])
        self.config['sources'][0]['root'] = 'wrong-path'
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'Empty source inventory'):
            self.run_update(selected=['community-a'])
        self.assertEqual(self.outputs(), before)
        self.config['sources'][0]['adapter'] = 'rst'
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'Unsupported adapter'):
            self.run_update(selected=['community-a'])

    def test_new_uncollected_source_and_offline_aggregate(self):
        self.run_update()
        third = copy.deepcopy(self.config['sources'][0])
        third.update(id='pytorch-fixture', label='PyTorch fixture', community='Fixture only', checkout='not-installed')
        self.config['sources'].insert(0, third)
        self.save_config()
        self.run_update(aggregate_only=True)
        self.assertIsNone(self.summary()['corpus']['pytorch-fixture']['included'])
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 4)
        self.assertEqual(self.run_update(aggregate_only=True)['filesChanged'], 0)

    def test_full_check_detects_changed_inputs_and_corrupt_state(self):
        self.run_update()
        self.assertEqual(self.run_update(check_full=True)['fullCheck'], 'passed')
        repo = self.sources / 'community-a'
        (repo / 'ko/a.md').write_text('기울기', encoding='utf8')
        self.move_ref()
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            self.run_update(selected=['community-a'], check_full=True)
        self.run_update(selected=['community-a'])
        state = usage.read_json(self.root / 'usage/state/community-a.json')
        state['documents']['community-a:ko/a.md']['counts']['gradient']['기울기'] += 1
        self.write_json('usage/state/community-a.json', state)
        with self.assertRaisesRegex(ValueError, 'Corrupt state'):
            self.run_update(aggregate_only=True)

    def add_sphinx_source(self, roots=('ko/guide', 'ko/recipe')):
        """Two translation roots of .rst and sphinx-gallery .py paired with one original root each."""
        repo = self.sources / 'sphinx-docs'
        files = {
            'ko/guide/intro.rst': '제목\n====\n\n기울기 문단의 기울기.\n\n.. code-block:: python\n\n   기울기 = 1\n',
            'ko/guide/example.py': '"""제목\n====\n\n독스트링의 기울기.\n"""\nimport torch\n\n# 코드 주석의 기울기\n\n' + '#' * 30 + '\n# 주석 블록의 기울기.\n',
            'ko/guide/helper.py': '# 독스트링 없는 기울기 코드\nimport torch\n',
            'ko/recipe/only-ko.rst': '번역만 있는 기울기.\n',
            'en/guide/intro.rst': 'Title\n=====\n',
            'en/guide/example.py': '"""Title"""\n',
            'en/guide/helper.py': 'import torch\n',
            'en/recipe/other.rst': 'Other\n=====\n',
        }
        for name, text in files.items():
            path = repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf8')
        self.git(repo, 'init', '-q')
        revision = self.commit(repo)
        self.config['sources'].append({
            'id': 'sphinx-docs', 'label': 'Sphinx docs', 'community': 'PyTorch',
            'repository': 'https://github.com/example/sphinx-docs', 'checkout': 'sphinx-docs',
            'ref': revision, 'root': list(roots), 'adapter': 'paired-sphinx', 'exclude': [],
            'original': {'repository': 'https://github.com/example/sphinx-docs', 'checkout': 'sphinx-docs',
                         'ref': revision, 'root': ['en/guide', 'en/recipe']},
        })
        self.save_config()

    def test_sphinx_source_scope_counts_and_evidence(self):
        self.run_update()
        preserved = {sid: (self.root / f'usage/state/{sid}.json').read_bytes() for sid in ('community-a', 'community-b')}
        self.add_sphinx_source()
        self.run_update(selected=['sphinx-docs'])
        state = usage.read_json(self.root / 'usage/state/sphinx-docs.json')
        reasons = sorted(doc['reason'] for doc in state['documents'].values())
        self.assertEqual(reasons, ['english-missing', 'not-a-gallery-document', 'paired-translation', 'paired-translation'])
        self.assertEqual(self.summary()['corpus']['sphinx-docs'], {'scanned': 4, 'included': 2})
        self.assertEqual(state['documents']['sphinx-docs:ko/guide/intro.rst']['enPath'], 'en/guide/intro.rst')
        # Prose only: reST code blocks, plain code comments and code-only files are not counted.
        usage_by_source = self.summary()['terms']['gradient']['bySource']['sphinx-docs']
        self.assertEqual(usage_by_source, {'occurrences': 4, 'documentCount': 2})
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 8)
        evidence = state['documents']['sphinx-docs:ko/guide/example.py']['evidence']['gradient']['기울기']
        self.assertEqual((evidence['line'], evidence['endLine']), (4, 4))
        for sid, before in preserved.items():
            self.assertEqual((self.root / f'usage/state/{sid}.json').read_bytes(), before)
        self.assertEqual(self.run_update(selected=['sphinx-docs'])['filesChanged'], 0)
        self.assertEqual(self.run_update(selected=['sphinx-docs'], check_full=True)['fullCheck'], 'passed')

    def test_repository_root_scope_pairs_and_excludes(self):
        """Documents that live at the repository root are configured with '.'."""
        for name, files in (('root-ko', {'model.md': '기울기 기울기', 'README.md': '기울기', 'docs/template.md': '기울기', 'only-ko.md': '기울기'}),
                            ('root-en', {'model.md': 'gradient', 'README.md': 'readme', 'docs/template.md': 'template'})):
            repo = self.sources / name
            for path, text in files.items():
                (repo / path).parent.mkdir(parents=True, exist_ok=True)
                (repo / path).write_text(text, encoding='utf8')
            self.git(repo, 'init', '-q')
            revision = self.commit(repo)
            if name == 'root-ko':
                translation = revision
        self.config['sources'].append({
            'id': 'root-docs', 'label': 'Root docs', 'community': 'Root', 'repository': 'https://github.com/example/root-ko',
            'checkout': 'root-ko', 'ref': translation, 'adapter': 'paired-markdown', 'root': '.',
            'exclude': ['README.md', 'docs/*'],
            'original': {'repository': 'https://github.com/example/root-en', 'checkout': 'root-en', 'ref': revision, 'root': '.'},
        })
        self.save_config()
        self.run_update(selected=['root-docs'])
        state = usage.read_json(self.root / 'usage/state/root-docs.json')
        self.assertEqual({doc['path']: doc['reason'] for doc in state['documents'].values()}, {
            'README.md': 'excluded-by-config', 'docs/template.md': 'excluded-by-config',
            'model.md': 'paired-translation', 'only-ko.md': 'english-missing'})
        self.assertEqual(state['documents']['root-docs:model.md']['enPath'], 'model.md')
        self.assertEqual(self.summary()['terms']['gradient']['bySource']['root-docs'], {'occurrences': 2, 'documentCount': 1})

    def test_sphinx_roots_must_pair_and_stay_inside_the_repository(self):
        self.add_sphinx_source()
        source = self.config['sources'][-1]
        source['original']['root'] = ['en/guide', 'en/recipe', 'en/extra']
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'Pair every translation root'):
            self.run_update(selected=['sphinx-docs'])
        source['original']['root'] = ['en/guide', 'en/recipe']
        source['root'] = ['ko/guide', '../outside']
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'Unsafe relative root'):
            self.run_update(selected=['sphinx-docs'])
        source['root'] = []
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'Translation root must be explicit'):
            self.run_update(selected=['sphinx-docs'])

    def test_config_exclusion_and_reinclude(self):
        self.run_update()
        self.config['sources'][0]['exclude'] = ['ko/*.md']
        self.save_config()
        self.run_update(selected=['community-a'])
        self.assertEqual(self.summary()['corpus']['community-a']['included'], 0)
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 2)
        self.config['sources'][0]['exclude'] = []
        self.save_config()
        self.run_update(selected=['community-a'])
        self.assertEqual(self.summary()['terms']['gradient']['occurrences'], 4)


if __name__ == '__main__':
    unittest.main()
