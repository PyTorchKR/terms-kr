#!/usr/bin/env python3
"""reStructuredText prose blocks for Sphinx sources; matching rules stay in usage_core."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys

# Also supports importlib-based tests without installing a Python package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from usage_core import canonical

# Text blocks of a sphinx-gallery example: the module docstring plus comment blocks that
# follow a `####...` (20+) or `# %%` header. Same split as sphinx-gallery 0.19.0
# py_source_parser.split_code_and_text_blocks, the version this corpus is built with.
GALLERY_TEXT = re.compile(r'(?P<header>^#{20,}.*|^# ?%%.*)\s(?P<text>(?:^#.*\s?)*)', re.M)
QUOTE = re.compile(r'[rRbBuU]{0,2}("""|\'\'\'|"|\')')

DIRECTIVE = re.compile(r'^(\s*)\.\.[ \t]+([A-Za-z0-9][\w.+:-]*)::(.*)$')
EXPLICIT = re.compile(r'^\s*\.\.([ \t]|$)')
OPTION = re.compile(r'^\s*:[A-Za-z][\w.+-]*:([ \t]|$)')
ADORNMENT = re.compile(r'^\s*([!-/:-@\[-`{-~])\1+\s*$')
SIMPLE_TABLE = re.compile(r'^\s*[=-]{2,}([ \t]+[=-]{2,})+\s*$')
DOCTEST = re.compile(r'^\s*>>>([ \t]|$)')
# Enumerators are ASCII in reST; Korean words ending in ")" or "." are prose, not list markers.
BULLET = re.compile(r'^\s*([-*+•]|\(?[0-9A-Za-z]{1,3}[.)])([ \t]|$)')

# Bodies of every other directive (code-block, image, literalinclude, math, raw, toctree, …)
# are excluded, like fenced code and images in Markdown. Unlisted directives stay excluded.
PROSE_DIRECTIVES = {
    'admonition', 'attention', 'card', 'caution', 'centered', 'compound', 'container',
    'danger', 'deprecated', 'epigraph', 'error', 'grid', 'grid-item', 'grid-item-card',
    'highlights', 'hint', 'important', 'list-table', 'note', 'only', 'pull-quote', 'rst-class',
    'rubric', 'sidebar', 'seealso', 'table', 'tab-item', 'tab-set', 'tip', 'topic',
    'versionadded', 'versionchanged', 'warning',
}


def strip_inline(text):
    """Drop markup that is not prose; every removal is a boundary, not an empty string."""
    text = re.sub(r'``.+?``', '\0', text, flags=re.S)
    text = re.sub(r':[\w.+-]+:`[^`]*`_{0,2}', '\0', text)
    # Hyperlinks keep their display text; the target is excluded like a Markdown URL.
    text = re.sub(r'`([^`<]*?)\s*<[^`>]*>`_{1,2}', r' \1 \0', text)
    text = re.sub(r'`([^`]*?)`_{1,2}', r' \1 ', text)
    text = re.sub(r'`[^`]*`', '\0', text)
    text = re.sub(r'\|[^|\s][^|]*\|', '\0', text)
    text = re.sub(r'\[[\w#*-]+\]_', '\0', text)
    text = re.sub(r'https?://[^\s|]+', '\0', text)
    text = re.sub(r'\*\*?', '', text)
    text = re.sub(r'\\(.)', r'\1', text)
    # Grid table cells and gallery navigation items must not be joined across the separator.
    return text.replace('|', '\0')


def body_end(lines, start, indent):
    """Index after the last line indented under lines[start]; trailing blanks stay outside."""
    index, end = start + 1, start + 1
    while index < len(lines):
        text = lines[index][1]
        if text.strip():
            if len(text) - len(text.lstrip()) <= indent:
                break
            end = index + 1
        index += 1
    return end


def prose_lines(lines):
    """Keep prose lines with their source line numbers; None separates blocks."""
    result, index, table, border = [], 0, False, False
    while index < len(lines):
        number, text = lines[index]
        stripped = text.strip()
        indent = len(text) - len(text.lstrip())
        index += 1
        if not stripped:
            result.append(None)
            table = table and not border  # a blank line after the closing border ends the table
            continue
        border = bool(SIMPLE_TABLE.match(text))
        directive = DIRECTIVE.match(text)
        if directive:
            result.append(None)
            if directive[2].lower() in PROSE_DIRECTIVES:
                if directive[3].strip():
                    result.append((number, directive[3]))
                while index < len(lines) and (not lines[index][1].strip() or OPTION.match(lines[index][1])):
                    index += 1
            else:
                index = body_end(lines, index - 1, indent)
            continue
        if EXPLICIT.match(text):  # comment, hyperlink target, footnote, substitution definition
            result.append(None)
            index = body_end(lines, index - 1, indent)
            continue
        if DOCTEST.match(text):
            result.append(None)
            while index < len(lines) and lines[index][1].strip():
                index += 1
            continue
        if stripped.endswith('::'):  # literal block: the paragraph stays, the block does not
            if stripped[:-2].strip():
                result.append((number, stripped[:-2]))
            else:
                result.append(None)
            index = body_end(lines, index - 1, indent)
            continue
        if border:
            table = True
            result.append(None)
            continue
        if ADORNMENT.match(text):  # section underline, transition, grid table border
            result.append(None)
            continue
        if table:  # column gaps are cell boundaries, not spaces inside a phrase
            result += [None, (number, re.sub(r'[ \t]{2,}', '\0', stripped)), None]
            continue
        bullet = BULLET.match(stripped)
        if bullet:  # each item is its own block; the marker itself is not prose
            result.append(None)
            stripped = stripped[bullet.end():].strip()
        if stripped:
            result.append((number, stripped))
    return result


def to_blocks(lines):
    result, group = [], []
    for item in [*prose_lines(lines), None]:
        if item:
            group.append(item)
            continue
        if group:
            start, end = group[0][0], group[-1][0]
            raw = '\n'.join(text for _, text in group)
            for part in strip_inline(' '.join(text for _, text in group)).split('\0'):
                if canonical(part):
                    result.append({'text': canonical(part), 'display': re.sub(r'\s+', ' ', part).strip(),
                                   'line': start, 'endLine': end, 'raw': raw})
        group = []
    return result


def rst_blocks(text):
    return to_blocks(list(enumerate(text.split('\n'), 1)))


def gallery_regions(text):
    """reST regions of a sphinx-gallery example with original 1-based line numbers."""
    lines = text.split('\n')
    node = module_docstring(ast.parse(text))
    if node is None:
        raise ValueError('sphinx-gallery examples require a module docstring')
    region = lines[node.lineno - 1:node.end_lineno]
    quote = QUOTE.match(region[0][node.col_offset:])
    region[0] = region[0][:node.col_offset] + ' ' * len(quote[0]) + region[0][node.col_offset + len(quote[0]):]
    region[-1] = re.sub(r'("""|\'\'\'|"|\')$', '', region[-1][:None if len(region) > 1 else node.end_col_offset].rstrip())
    regions = [list(enumerate(region, node.lineno))]
    rest = '\n'.join(lines[node.end_lineno:])
    for match in GALLERY_TEXT.finditer(rest):
        body = [re.sub(r'^#', '', line) for line in match['text'].split('\n')]
        margin = min((len(line) - len(line.lstrip()) for line in body if line.strip()), default=0)
        start = node.end_lineno + rest.count('\n', 0, match.start()) + 2  # after the header line
        regions.append(list(enumerate((line[margin:] for line in body), start)))
    return regions


def module_docstring(module):
    first = module.body[0] if module.body else None
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first.value
    return None


def gallery_blocks(text):
    return [block for region in gallery_regions(text) for block in to_blocks(region)]


def is_gallery_document(text):
    """Sphinx-gallery requires a module docstring; other .py files are plain code."""
    try:
        return module_docstring(ast.parse(text)) is not None
    except SyntaxError:
        return False


EXTRACTORS = {'.rst': rst_blocks, '.py': gallery_blocks}


def extractor_for(path):
    suffix = path[path.rindex('.'):] if '.' in path else ''
    if suffix not in EXTRACTORS:
        raise ValueError(f'No Sphinx source extractor for {path}')
    return EXTRACTORS[suffix]
