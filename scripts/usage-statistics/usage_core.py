#!/usr/bin/env python3
"""Shared, versioned prose matching; source adapters must not change these rules."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from collections import Counter

from markdown_it import MarkdownIt
RULE = 'ko-surface-v2.1'
MD = MarkdownIt('commonmark', {'html': True}).enable('table')


def canonical(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', value).lower()).strip()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def tree(repo, commit, *paths):
    result = {}
    for record in git(repo, 'ls-tree', '-r', '-z', '--full-tree', commit, '--', *paths).split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, kind, sha = metadata.decode().split()
        if kind == 'blob' and mode in ('100644', '100755'):
            result[name.decode('utf8')] = sha
    if not result:
        raise ValueError(f'Empty source inventory: {repo}')
    return result


def blobs(repo, shas):
    """Read an explicit set of blobs in one Git process; missing blobs fail the run."""
    shas = sorted(set(shas))
    if not shas:
        return {}
    raw = subprocess.check_output(['git', '-C', str(repo), 'cat-file', '--batch'], input=('\n'.join(shas) + '\n').encode())
    offset, result = 0, {}
    for requested in shas:
        end = raw.index(b'\n', offset)
        header = raw[offset:end].decode().split()
        if len(header) != 3 or header[0] != requested or header[1] != 'blob':
            raise ValueError(f'Unreadable blob: {requested}')
        length = int(header[2])
        result[requested] = raw[end + 1:end + 1 + length].decode('utf8', errors='strict')
        offset = end + length + 2
    return result


def frontmatter(text):
    match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|$)', text, re.S)
    if not match:
        return {}, text
    values = {}
    for line in match[1].splitlines():
        item = re.match(r'^([\w-]+):\s*(.*?)\s*$', line)
        if item:
            values[item[1]] = item[2].strip('\"\'')
    # Blank lines preserve source line numbers.
    return values, '\n' * match[0].count('\n') + text[match.end():]


def blocks(text):
    """Prose only; excluded inline content is a boundary, not an empty string."""
    _, text = frontmatter(text)
    text = re.sub(r'<!--.*?-->', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    text = re.sub(r'\[\[[^\]\n]+\]\]', '', text)
    text = re.sub(r'^\s*\[!(?:TIP|NOTE|WARNING|IMPORTANT|CAUTION)\]\s*', '', text, flags=re.M)
    lines = text.splitlines()
    result = []
    enclosing = [0, 1]
    for token in MD.parse(text):
        if token.map:
            enclosing = token.map
        if token.type != 'inline':
            continue
        start, end = token.map or enclosing
        parts = []
        for child in token.children or []:
            if child.type == 'text':
                parts.append(child.content)
            elif child.type in ('softbreak', 'hardbreak'):
                parts.append(' ')
            elif child.type in ('code_inline', 'image', 'html_inline'):
                parts.append('\0')
        # URL targets are absent from text nodes. Exclude literal URLs and API directives.
        prose = re.sub(r'https?://[^\s\0]+', '\0', ''.join(parts))
        if prose.lstrip().startswith(('[[', '[autodoc]', '[[')):
            continue
        for part in prose.split('\0'):
            if canonical(part):
                result.append({'text': canonical(part), 'display': re.sub(r'\s+', ' ', part).strip(), 'line': start + 1, 'endLine': max(start + 1, end), 'raw': '\n'.join(lines[start:end])})
    return result


def compile_patterns(candidates):
    result = {}
    for term, entry in candidates.items():
        mapping = {canonical(v): v for v in entry['variants']}
        if mapping:
            choices = sorted(mapping, key=lambda v: (-len(v), v))
            result[term] = (re.compile('|'.join(re.escape(v) for v in choices)), mapping)
    return result


def count_document(text, patterns, extract=blocks):
    """Matching is shared by every source format; only block extraction differs."""
    counts, evidence = {}, {}
    for block in extract(text):
        for term, (pattern, mapping) in patterns.items():
            for match in pattern.finditer(block['text']):
                label = mapping[match[0]]
                counts.setdefault(term, {})[label] = counts.get(term, {}).get(label, 0) + 1
                if label not in evidence.setdefault(term, {}):
                    # Anchor the containing paragraph/table, not a guessed exact character line.
                    excerpt = block['text'][max(0, match.start() - 55):match.end() + 85]
                    evidence[term][label] = {'line': block['line'], 'endLine': block['endLine'], 'excerpt': excerpt}
    return counts, evidence


def update_records(documents, previous, compatible, read_texts, candidates, counted_at, extract_for=None):
    records, metrics = {}, Counter()
    extract_for = extract_for or (lambda document: blocks)
    patterns = compile_patterns(candidates)
    pending = {}
    for key, doc in documents.items():
        old = previous.get(key)
        if not doc['eligible']:
            records[key] = {**doc, 'counts': {}, 'evidence': {}, 'countedAt': None}
            metrics['excluded'] += 1
        elif compatible and old and old['eligible'] and old['blobSha'] == doc['blobSha']:
            records[key] = {**doc, 'counts': old['counts'], 'evidence': old['evidence'], 'countedAt': old['countedAt']}
            metrics['reused'] += 1
        else:
            pending[key] = doc
    texts = read_texts(pending)
    for key, doc in pending.items():
        counts, evidence = count_document(texts[key], patterns, extract_for(doc))
        records[key] = {**doc, 'counts': counts, 'evidence': evidence, 'countedAt': counted_at}
        metrics['recounted'] += 1
    metrics['deleted'] = len(set(previous) - set(documents))
    return dict(sorted(records.items())), dict(metrics)
