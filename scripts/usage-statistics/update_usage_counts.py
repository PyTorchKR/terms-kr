#!/usr/bin/env python3
"""Update selected translation sources from pinned local Git blobs; never fetch/push."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from importlib.metadata import version
from pathlib import Path
import json
import re
import sys
from urllib.parse import quote

# Also supports importlib-based tests without installing a Python package.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rst_source import extractor_for, is_gallery_document
from usage_core import (RULE, blobs, blocks, canonical, compile_patterns, count_document,
                        digest, frontmatter, git, read_json, tree, update_records)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 2
ADAPTERS = {'paired-markdown': 1, 'krew-blog': 1, 'paired-sphinx': 1, 'pytorch-blog': 1}
SUFFIXES = {'paired-markdown': ('.md',), 'krew-blog': ('.md',), 'paired-sphinx': ('.rst', '.py'), 'pytorch-blog': ('.md',)}
# Markdown keeps the shared extractor; Sphinx sources pick one per file format.
BLOCKS = {'paired-markdown': lambda document: blocks, 'krew-blog': lambda document: blocks,
          'paired-sphinx': lambda document: extractor_for(document['path']), 'pytorch-blog': lambda document: blocks}
PAIRED = ('paired-markdown', 'paired-sphinx')
FROM_FRONTMATTER = ('krew-blog', 'pytorch-blog')
# A post whose original is only on the web is still a translation; the reason says which evidence was used.
INCLUDED = ('paired-translation', 'linked-translation')


def candidate_set(root):
    entries = [t for f in read_json(root / 'data/index.json') for t in read_json(root / 'data' / f)]
    options = read_json(root / 'usage/variants.json')
    if options['schemaVersion'] != 1:
        raise ValueError('Unsupported variants schema')
    extras = {canonical(k): v for k, v in options['extraVariants'].items()}
    tracked = {canonical(t) for t in options['showWhenUnmatched']}
    result = {}
    for entry in entries:
        labels = [v for m in entry['meanings'] for v in [m['korean'], *m.get('synonyms', [])]]
        labels += extras.get(canonical(entry['term']), [])
        unique = {}
        for label in labels:
            if not isinstance(label, str) or not canonical(label):
                raise ValueError('Candidate spellings must be nonempty strings')
            unique.setdefault(canonical(label), label)
        supported = sorted((v for k, v in unique.items() if re.search('[가-힣]', k)), key=canonical)
        result[entry['term']] = {
            'variants': supported,
            'unsupportedVariants': sorted((v for v in unique.values() if v not in supported), key=canonical),
            'showWhenUnmatched': canonical(entry['term']) in tracked,
        }
    return result


def roots(spec):
    """One document root, or several; single-root configs stay plain strings."""
    return spec['root'] if isinstance(spec['root'], list) else [spec['root']]


def root_prefix(root):
    """Whole-repository scope is written as '.'; any other root is a directory prefix."""
    return '' if root in ('', '.') else root.rstrip('/') + '/'


def paired_roots(source):
    """Each translation root prefix with the original root prefix it maps to."""
    originals = [root_prefix(root) for root in roots(source['original'])]
    return {root_prefix(root): originals[index if len(originals) > 1 else 0] for index, root in enumerate(roots(source))}


def load_config(root):
    config = read_json(root / 'usage/sources.json')
    if config['schemaVersion'] != 1:
        raise ValueError('Unsupported sources schema')
    sources = {}
    for source in config['sources']:
        sid = source['id']
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', sid) or sid in sources:
            raise ValueError(f'Invalid/duplicate source id: {sid}')
        if source['adapter'] not in ADAPTERS:
            raise ValueError(f'Unsupported adapter: {source["adapter"]}; do not parse RST/MDX as Markdown')
        for repository in (source, source['original']):
            if not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+', repository['repository']):
                raise ValueError('Only public GitHub source URLs are supported')
            if not re.fullmatch(r'[0-9a-f]{40}', repository['ref']):
                raise ValueError('Pin each source ref to a full Git commit SHA')
            for field, path in [('checkout', repository['checkout']), *(('root', value) for value in roots(repository))]:
                if not isinstance(path, str) or path.startswith(('/', '-')) or '..' in path.split('/') or '\\' in path:
                    raise ValueError(f'Unsafe relative {field}: {path}')
            if not repository['checkout']:
                raise ValueError('checkout must be a relative directory')
        if not roots(source) or not all(roots(source)):
            raise ValueError('Translation root must be explicit')
        if len(roots(source['original'])) not in (1, len(roots(source))):
            raise ValueError('Pair every translation root with one original root')
        if not isinstance(source['exclude'], list) or not all(isinstance(p, str) for p in source['exclude']):
            raise ValueError('exclude must be a list of path globs')
        if not source['label'] or not source['community']:
            raise ValueError('Source label and community are required')
        sources[sid] = source
    if not sources:
        raise ValueError('At least one source must be registered')
    return sources


def policy_hash(source):
    # Moving a pinned revision must not invalidate unchanged document counts.
    value = {**source, 'ref': None, 'original': {**source['original'], 'ref': None}}
    return digest({'source': value, 'adapterVersion': ADAPTERS[source['adapter']], 'rule': RULE})


def source_inventory(source, sources_dir):
    inventories, commits = [], []
    for spec in (source, source['original']):
        repo = sources_dir / spec['checkout']
        commit = git(repo, 'rev-parse', '--verify', spec['ref'] + '^{commit}').decode().strip()
        inventories.append(tree(repo, commit, *[root or '.' for root in roots(spec)]))
        commits.append(commit)
    ko_tree, en_tree = inventories
    originals = paired_roots(source)
    suffixes = SUFFIXES[source['adapter']]
    paths = {p: sha for p, sha in ko_tree.items() if p.endswith(suffixes) and any(p.startswith(prefix) for prefix in originals)}
    # Empty/mistyped roots and unsupported-only corpora fail instead of replacing old data with zeros.
    if not paths:
        raise ValueError(f'No {"/".join(suffixes)} translations in {source["id"]}; check root/format before removing its snapshot')
    # Only formats whose eligibility depends on the body are read here.
    needed = [sha for path, sha in paths.items() if source['adapter'] in FROM_FRONTMATTER or path.endswith('.py')]
    texts = blobs(sources_dir / source['checkout'], needed) if needed else {}
    # Blog posts pair by URL slug because Korean and English date prefixes differ.
    en_posts = {re.sub(r'^\d{4}-\d{2}-\d{2}-', '', p.rsplit('/', 1)[-1])[:-3]: p for p in sorted(en_tree) if p.endswith('.md')}
    documents = {}
    for path, sha in sorted(paths.items()):
        reason, en_path = 'paired-translation', None
        extra = {}
        if source['adapter'] in PAIRED:  # paired-markdown and paired-sphinx share the path mapping
            prefix = next(p for p in originals if path.startswith(p))
            en_path = originals[prefix] + path[len(prefix):]
            if en_path not in en_tree:
                reason, en_path = 'english-missing', None
            elif path.endswith('.py') and not is_gallery_document(texts[sha]):
                reason = 'not-a-gallery-document'
        elif source['adapter'] == 'pytorch-blog':
            # pytorch.kr posts declare their original in frontmatter and quote it paragraph by paragraph.
            fm, _ = frontmatter(texts[sha])
            link = fm.get('org_link', '')
            categories = [value.strip(' "\'') for value in fm.get('category', '').strip('[]').split(',')]
            slug = link.rstrip('/').rsplit('/', 1)[-1] if link.startswith('https://pytorch.org/blog/') else ''
            extra = {'originalLink': link}
            if not slug or 'translation' not in categories:
                reason = 'english-missing'
            else:
                en_path = en_posts.get(slug)
                # The English Markdown left pytorch.github.io in 2025-08; the published original did not.
                reason = 'paired-translation' if en_path else 'linked-translation'
        elif source['adapter'] == 'krew-blog':
            text = texts[sha]
            fm, _ = frontmatter(text)
            source_url = fm.get('source_url', '')
            if not source_url.startswith('https://huggingface.co/blog/'):
                match = re.search(r'https://huggingface\.co/blog/[A-Za-z0-9._~/%+-]+', text[:3000])
                source_url = match[0].rstrip('/)') if match else ''
            slug = source_url.split('/blog/', 1)[-1].strip('/') if source_url else ''
            en_path = next((p for p in (slug + '.md', slug.split('/')[-1] + '.md') if p in en_tree), None)
            status = fm.get('translation_status', 'published')
            extra = {'translationStatus': status}
            if status.lower() == 'draft':
                reason = 'draft'
            elif not source_url or not en_path:
                reason = 'english-missing'
            elif '번역한 글입니다' not in text[:3500]:
                reason = 'translation-notice-missing'
        else:
            raise ValueError(f'No inventory rule for adapter: {source["adapter"]}')
        if any(fnmatchcase(path, pattern) for pattern in source['exclude']):
            reason = 'excluded-by-config'
        documents[f'{source["id"]}:{path}'] = {
            'source': source['id'], 'path': path, 'blobSha': sha, 'eligible': reason in INCLUDED,
            'reason': reason, 'enPath': en_path, **extra,
        }
    return commits, documents


def update_source(source, previous, candidates, sources_dir, now, full=False):
    commits, inventory = source_inventory(source, sources_dir)
    candidate_hash = digest(candidates)
    policy = policy_hash(source)
    compatible = previous.get('candidateHash') == candidate_hash and previous.get('policyHash') == policy
    def read_pending(pending):
        contents = blobs(sources_dir / source['checkout'], (d['blobSha'] for d in pending.values()))
        return {key: contents[d['blobSha']] for key, d in pending.items()}
    documents, metrics = update_records(inventory, previous.get('documents', {}), compatible and not full, read_pending, candidates, now, BLOCKS[source['adapter']])
    input_hash = digest({'config': source, 'commits': commits, 'inventory': inventory, 'candidates': candidates, 'policy': policy})
    if full:
        if previous.get('inputHash') != input_hash:
            raise ValueError(f'{source["id"]}: inputs changed; update before --check-full')
        for key, doc in documents.items():
            old = previous['documents'][key]
            if doc['counts'] != old['counts'] or doc['evidence'] != old['evidence']:
                raise ValueError(f'Full recount differs: {key}')
        return previous, metrics
    if previous.get('inputHash') == input_hash:
        return previous, metrics
    state = {
        'schemaVersion': SCHEMA, 'configHash': digest(source), 'candidateHash': candidate_hash,
        'countingRuleVersion': RULE, 'policyHash': policy, 'inputHash': input_hash,
        'generatedAt': now, 'source': {**source, 'commit': commits[0], 'original': {**source['original'], 'commit': commits[1]}},
        'documents': documents,
    }
    return {**state, 'snapshotId': digest(state)}, metrics


def checked_states(root, config, replacements=None):
    states = {}
    for sid in config:
        path = root / 'usage/state' / f'{sid}.json'
        if replacements and sid in replacements:
            states[sid] = replacements[sid]
        elif path.exists():
            states[sid] = read_json(path)
    return states


def aggregate(config, states, candidates):
    candidate_hash = digest(candidates)
    sources, corpus = {}, {}
    for sid, spec in config.items():
        state = states.get(sid)
        if state:
            if state['schemaVersion'] != SCHEMA or state['candidateHash'] != candidate_hash or state['configHash'] != digest(spec) or state['policyHash'] != policy_hash(spec) or state['countingRuleVersion'] != RULE:
                raise ValueError(f'Stale snapshot for {sid}: update this source too; incompatible sources cannot be mixed')
            if digest({k: v for k, v in state.items() if k != 'snapshotId'}) != state['snapshotId']:
                raise ValueError(f'Corrupt state: {sid}')
        docs = state['documents'] if state else {}
        sources[sid] = {
            'label': spec['label'], 'community': spec['community'], 'repository': spec['repository'],
            'status': 'collected' if state else 'not-collected',
            'commit': state['source']['commit'] if state else None,
            'generatedAt': state['generatedAt'] if state else None,
            'snapshotId': state['snapshotId'] if state else None,
        }
        corpus[sid] = {
            'scanned': len(docs) if state else None,
            'included': sum(d['eligible'] for d in docs.values()) if state else None,
        }
    any_corpus = any((c['included'] or 0) > 0 for c in corpus.values())
    terms = {}
    for term, candidate in candidates.items():
        variants, seen = [], set()
        for spelling in candidate['variants']:
            evidence = []
            by_source = {sid: (0 if sid in states else None) for sid in config}
            for sid, state in states.items():
                for key, doc in state['documents'].items():
                    count = doc['counts'].get(term, {}).get(spelling, 0)
                    if not doc['eligible'] or not count:
                        continue
                    if type(count) is not int or count < 1:
                        raise ValueError(f'Invalid count: {key}')
                    item = doc['evidence'][term][spelling]
                    url = f'{sources[sid]["repository"]}/blob/{sources[sid]["commit"]}/{quote(doc["path"], safe="/")}#L{item["line"]}-L{item["endLine"]}'
                    evidence.append({'id': key, 'source': sid, 'path': doc['path'], 'occurrences': count, 'url': url, **item})
                    by_source[sid] += count
                    seen.add(key)
            variants.append({'korean': spelling, 'occurrences': sum(v or 0 for v in by_source.values()), 'documentCount': len(evidence), 'bySource': by_source, 'documents': evidence})
        by_source = {sid: {
            'occurrences': sum(v['bySource'][sid] or 0 for v in variants) if sid in states else None,
            'documentCount': sum(k.startswith(sid + ':') for k in seen) if sid in states else None,
        } for sid in config}
        total = sum(v['occurrences'] for v in variants)
        status = 'unsupported' if not variants else ('not-collected' if not any_corpus else ('matched' if total else 'no-match'))
        terms[term] = {**{k: v for k, v in candidate.items() if k != 'variants'}, 'status': status,
                       'occurrences': total, 'documentCount': len(seen), 'bySource': by_source, 'variants': variants}
    inputs = {'config': config, 'candidateHash': candidate_hash, 'states': {sid: s['snapshotId'] for sid, s in states.items()}, 'rule': RULE}
    return {'schemaVersion': SCHEMA, 'snapshotId': digest(inputs), 'countingRuleVersion': RULE,
            'candidateHash': candidate_hash, 'generatedAt': max((s['generatedAt'] for s in states.values()), default=None),
            'sources': sources, 'corpus': corpus, 'terms': terms}


def rendered_outputs(root, config, states, summary):
    lines = ['# 번역 표기 통계 — 스캔 기록', '', f'스냅샷: {summary["snapshotId"]}', f'집계 규칙: {RULE}', '',
             '한국어 문자열의 단순 출현 수이며 영문 용어와의 번역 대응·선호도를 뜻하지 않는다.',
             '미수집 출처는 0회가 아니다. 원격 최신 문서가 아니라 아래 고정 커밋을 사용했다.',
             '자세한 규칙과 출처 추가 절차: docs/usage-statistics/.', '', '## 소스별 기준', '']
    for sid, source in config.items():
        state = states.get(sid)
        if not state:
            lines.append(f'- {source["label"]}: 미수집')
            continue
        info = state['source']
        original = info['original']
        lines += [f'- {source["label"]}: [{info["commit"]}]({info["repository"]}/tree/{info["commit"]}), 집계 {state["generatedAt"]}',
                  f'  - 영문 대응: [{original["commit"]}]({original["repository"]}/tree/{original["commit"]})']
    lines += ['', '## 문서 목록', '', '| 소스 | 문서 | 포함 | 이유 | 마지막 본문 집계(UTC) |', '| --- | --- | --- | --- | --- |']
    for sid, state in states.items():
        for doc in state['documents'].values():
            source = state['source']
            url = f'{source["repository"]}/blob/{source["commit"]}/{quote(doc["path"], safe="/")}'
            path = doc['path'].replace('|', '\\|')
            lines.append(f'| {sid} | [{path}]({url}) | {"포함" if doc["eligible"] else "제외"} | {doc["reason"]} | {doc["countedAt"] or "—"} |')
    json_text = lambda value: json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    return {**{root / 'usage/state' / f'{sid}.json': json_text(state) for sid, state in states.items()},
            root / 'public/usage/term-usage.json': json_text(summary), root / 'public/usage/scanned.md': '\n'.join(lines) + '\n'}


def run(root, sources_dir, selected=None, check_full=False, aggregate_only=False):
    config, candidates = load_config(root), candidate_set(root)
    selected = selected if selected is not None else list(config)
    if set(selected) - set(config):
        raise ValueError(f'Unknown source ids: {set(selected) - set(config)}')
    states = checked_states(root, config)
    metrics, replacements = {}, {}
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    if not aggregate_only:
        for sid in selected:
            replacements[sid], metrics[sid] = update_source(config[sid], states.get(sid, {}), candidates, sources_dir, now, check_full)
    states.update(replacements)
    states = {sid: states[sid] for sid in config if sid in states}
    summary = aggregate(config, states, candidates)  # Fail before any writes, including stale unselected sources.
    outputs = rendered_outputs(root, config, states, summary)
    if check_full:
        if any(not p.exists() or p.read_text(encoding='utf8') != content for p, content in outputs.items()):
            raise ValueError('Published outputs differ; run update or --aggregate-only first')
        return {'fullCheck': 'passed', 'sources': metrics}
    staged = []
    for path, content in outputs.items():
        if path.exists() and path.read_text(encoding='utf8') == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(content, encoding='utf8')
        staged.append((temporary, path))
    # One writer at a time. Each file is atomic, not the whole set; build validates cross-file integrity.
    for temporary, path in staged:
        temporary.replace(path)
    return {'snapshotId': summary['snapshotId'], 'filesChanged': len(staged), 'sources': metrics,
            'terms': len(summary['terms']), 'matched': sum(t['status'] == 'matched' for t in summary['terms'].values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources-dir', type=Path, default=ROOT.parent, help='Parent of configured local checkout directories')
    parser.add_argument('--source', action='append', help='Update only this source; repeat to select several')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-full', action='store_true', help='Read-only full recount of selected sources and output validation')
    mode.add_argument('--aggregate-only', action='store_true', help='Rebuild public output from compatible committed states; no source repositories needed')
    args = parser.parse_args()
    if version('markdown-it-py') != '3.0.0':
        raise ValueError('Install scripts/usage-statistics/requirements.txt for the pinned parser')
    print(json.dumps(run(ROOT, args.sources_dir.resolve(), args.source, args.check_full, args.aggregate_only)))


if __name__ == '__main__':
    main()
