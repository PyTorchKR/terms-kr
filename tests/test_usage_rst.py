"""Sphinx sources: only reST prose and sphinx-gallery text blocks are counted."""
import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/usage-statistics'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rst_source = load('rst_source')
usage_core = load('usage_core')

RST = '''\
텐서(Tensor) 소개
=================

.. 이 주석의 텐서는 세지 않는다.

``텐서`` 는 인라인 코드이고, `텐서 문서 <https://pytorch.kr/텐서>`_ 의 표시 문구는
본문이며 :class:`torch.텐서` 는 API 지시문이다.

.. note::

   참고 상자의 텐서도 본문이다.

.. code-block:: python

   # 코드 블록의 텐서는 세지 않는다
   텐서 = 1

다음 예시를 보자::

   여기 텐서는 리터럴 블록이다.

- 첫째 텐서 항목
- 둘째 항목

.. image:: 텐서.png
   :alt: 텐서 그림
'''

GALLERY = '''\
# -*- coding: utf-8 -*-
"""
텐서(Tensor) 다루기
===================

모듈 독스트링의 텐서는 본문이다.
"""
import torch

# 이 코드 주석의 텐서는 세지 않는다
텐서 = torch.tensor([1])


######################################################################
# 구분선 뒤 주석 블록의 텐서는 본문이다.
#
# ``텐서`` 는 인라인 코드다.

def f():
    """함수 독스트링의 텐서는 코드다."""
    return 1


# %%
# 퍼센트 구분선 뒤의 텐서도 본문이다.

####
# 짧은 구분선은 sphinx-gallery의 본문 구분자가 아니므로 이 텐서는 코드 주석이다.
print(텐서)
'''


class RstTests(unittest.TestCase):
    def counts(self, text, extract, spellings=('텐서',)):
        patterns = usage_core.compile_patterns({'tensor': {'variants': list(spellings)}})
        return usage_core.count_document(text, patterns, extract)

    def test_rst_counts_prose_and_excludes_markup(self):
        counts, evidence = self.counts(RST, rst_source.rst_blocks)
        # Title, link display text, note body, first bullet item.
        self.assertEqual(counts, {'tensor': {'텐서': 4}})
        self.assertEqual(evidence['tensor']['텐서']['line'], 1)

    def test_rst_line_ranges_point_at_the_paragraph(self):
        blocks = rst_source.rst_blocks(RST)
        note = next(b for b in blocks if '참고 상자' in b['text'])
        self.assertEqual((note['line'], note['endLine']), (11, 11))
        bullets = [b for b in blocks if '항목' in b['text']]
        self.assertEqual([(b['line'], b['endLine']) for b in bullets], [(22, 22), (23, 23)])

    def test_rst_cells_and_inline_markup_are_boundaries(self):
        table = '+------+------+\n| 텐서 | 곱   |\n+------+------+\n\n=====  =====\n텐서   곱\n=====  =====\n'
        self.assertEqual(self.counts(table, rst_source.rst_blocks, ('텐서 곱',))[0], {})
        self.assertEqual(self.counts('``텐서``\\ 곱', rst_source.rst_blocks, ('텐서 곱', '텐서'))[0], {})

    def test_rst_keeps_overlapping_and_wrapped_candidates(self):
        text = '기울기와 경사하강법, 그리고 줄바꿈된\n기울기 표기.\n'
        self.assertEqual(self.counts(text, rst_source.rst_blocks, ('기울기', '경사'))[0],
                         {'tensor': {'기울기': 2, '경사': 1}})

    def test_gallery_counts_docstring_and_delimited_comment_blocks(self):
        counts, evidence = self.counts(GALLERY, rst_source.gallery_blocks)
        # Module docstring title and body, `####` block, `# %%` block.
        self.assertEqual(counts, {'tensor': {'텐서': 4}})
        self.assertEqual(evidence['tensor']['텐서']['line'], 3)

    def test_gallery_block_line_numbers_follow_the_source_file(self):
        blocks = rst_source.gallery_blocks(GALLERY)
        hashes = next(b for b in blocks if '구분선 뒤' in b['text'])
        percent = next(b for b in blocks if '퍼센트' in b['text'])
        self.assertEqual((hashes['line'], hashes['endLine']), (15, 15))
        self.assertEqual((percent['line'], percent['endLine']), (25, 25))

    def test_plain_python_files_are_not_gallery_documents(self):
        self.assertFalse(rst_source.is_gallery_document('import torch\n# 텐서\n'))
        self.assertFalse(rst_source.is_gallery_document('def f(:\n'))
        self.assertTrue(rst_source.is_gallery_document(GALLERY))

    def test_extractor_is_chosen_by_file_suffix(self):
        self.assertIs(rst_source.extractor_for('a/b.rst'), rst_source.rst_blocks)
        self.assertIs(rst_source.extractor_for('a/b.py'), rst_source.gallery_blocks)
        with self.assertRaises(ValueError):
            rst_source.extractor_for('a/b.ipynb')


if __name__ == '__main__':
    unittest.main()
