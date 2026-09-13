import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync } from 'node:fs'

const path = p => new URL(`../${p}`, import.meta.url)
const read = p => JSON.parse(readFileSync(path(p), 'utf8'))
// Python sorts Unicode code points, not JavaScript UTF-16 code units.
const compare = (a, b) => {
  const left = [...a].map(c => c.codePointAt(0)), right = [...b].map(c => c.codePointAt(0))
  for (let i = 0; i < Math.min(left.length, right.length); i++) {
    if (left[i] !== right[i]) return left[i] - right[i]
  }
  return left.length - right.length
}
// Same canonical JSON as Python json.dumps(sort_keys=True, ensure_ascii=False).
const stable = v => Array.isArray(v) ? `[${v.map(stable).join(', ')}]`
  : v !== null && typeof v === 'object' ? `{${Object.keys(v).sort(compare).map(k => `${JSON.stringify(k)}: ${stable(v[k])}`).join(', ')}}` : JSON.stringify(v)
const hash = v => createHash('sha256').update(stable(v)).digest('hex')
// Match Python str whitespace, including NEL/control separators but excluding BOM.
const normalized = v => v.normalize('NFC').toLowerCase().replace(/[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/gu, ' ').replace(/^ | $/gu, '')
const sorted = v => [...v].sort()
const rule = readFileSync(path('scripts/usage_core.py'), 'utf8').match(/^RULE = '([^']+)'/m)[1]
const input = read('usage/variants.json')
const registry = read('usage/sources.json')
assert.equal(input.schemaVersion, 1)
assert.equal(registry.schemaVersion, 1)
const config = Object.fromEntries(registry.sources.map(s => [s.id, s]))
assert.equal(Object.keys(config).length, registry.sources.length, 'Duplicate source id')
const summary = read('public/usage/term-usage.json')
const terms = read('data/index.json').flatMap(f => read(`data/${f}`))
const extras = Object.fromEntries(Object.entries(input.extraVariants).map(([k, v]) => [normalized(k), v]))
const candidates = Object.fromEntries(terms.map(term => {
  const labels = [...term.meanings.flatMap(m => [m.korean, ...(m.synonyms ?? [])]), ...(extras[normalized(term.term)] ?? [])]
  const unique = new Map()
  labels.forEach(label => { if (!unique.has(normalized(label))) unique.set(normalized(label), label) })
  const byName = (a, b) => compare(normalized(a), normalized(b))
  return [term.term, {
    variants: [...unique.values()].filter(v => /[가-힣]/u.test(normalized(v))).sort(byName),
    unsupportedVariants: [...unique.values()].filter(v => !/[가-힣]/u.test(normalized(v))).sort(byName),
    showWhenUnmatched: input.showWhenUnmatched.some(v => normalized(v) === normalized(term.term)),
  }]
}))
const candidateHash = hash(candidates)
assert.equal(summary.schemaVersion, 2)
assert.equal(summary.countingRuleVersion, rule)
assert.equal(summary.candidateHash, candidateHash, 'Candidates changed; recount all collected sources')
assert.deepEqual(sorted(Object.keys(summary.terms)), sorted(Object.keys(candidates)))
assert.deepEqual(sorted(Object.keys(summary.sources)), sorted(Object.keys(config)))
assert.deepEqual(sorted(Object.keys(summary.corpus)), sorted(Object.keys(config)))
const states = {}, documents = {}, stateIds = {}
for (const [sid, spec] of Object.entries(config)) {
  assert.match(sid, /^[a-z0-9]+(?:-[a-z0-9]+)*$/)
  const exists = existsSync(path(`usage/state/${sid}.json`))
  const state = exists ? read(`usage/state/${sid}.json`) : null
  const source = summary.sources[sid]
  const { label, community, repository } = spec
  if (!state) {
    assert.deepEqual(source, { label, community, repository, status: 'not-collected', commit: null, generatedAt: null, snapshotId: null })
    assert.deepEqual(summary.corpus[sid], { scanned: null, included: null })
    continue
  }
  states[sid] = state
  stateIds[sid] = state.snapshotId
  const { snapshotId, ...payload } = state
  assert.equal(hash(payload), snapshotId, `Corrupt state: ${sid}`)
  assert.equal(state.schemaVersion, 2)
  assert.equal(state.countingRuleVersion, rule)
  assert.equal(state.configHash, hash(spec), `Stale source config: ${sid}`)
  assert.equal(state.candidateHash, candidateHash, `Stale source candidates: ${sid}`)
  assert.equal(state.source.commit, spec.ref)
  assert.equal(state.source.original.commit, spec.original.ref)
  assert.ok(!Number.isNaN(Date.parse(state.generatedAt)))
  assert.deepEqual(source, { label, community, repository, status: 'collected', commit: spec.ref, generatedAt: state.generatedAt, snapshotId })
  const docs = Object.values(state.documents)
  assert.deepEqual(summary.corpus[sid], { scanned: docs.length, included: docs.filter(d => d.eligible).length })
  for (const [id, doc] of Object.entries(state.documents)) {
    assert.equal(id, `${sid}:${doc.path}`)
    assert.equal(doc.source, sid)
    assert.match(doc.blobSha, /^[a-f0-9]{40}$/)
    documents[id] = doc
    if (!doc.eligible) {
      assert.deepEqual(doc.counts, {})
      assert.deepEqual(doc.evidence, {})
    }
    assert.deepEqual(sorted(Object.keys(doc.counts)), sorted(Object.keys(doc.evidence)))
    for (const [term, spellings] of Object.entries(doc.counts)) {
      assert.ok(candidates[term], `Unknown counted term: ${term}`)
      assert.deepEqual(sorted(Object.keys(spellings)), sorted(Object.keys(doc.evidence[term])))
      for (const [spelling, count] of Object.entries(spellings)) {
        assert.ok(candidates[term].variants.includes(spelling))
        assert.ok(Number.isInteger(count) && count > 0)
        const evidence = doc.evidence[term][spelling]
        assert.ok(Number.isInteger(evidence.line) && evidence.line >= 1)
        assert.ok(Number.isInteger(evidence.endLine) && evidence.endLine >= evidence.line)
        assert.equal(typeof evidence.excerpt, 'string')
      }
    }
  }
}
assert.equal(summary.snapshotId, hash({ config, candidateHash, states: stateIds, rule }))
assert.equal(summary.generatedAt, Object.values(states).map(s => s.generatedAt).sort().at(-1) ?? null)
const hasCorpus = Object.values(summary.corpus).some(c => c.included > 0)
for (const [term, candidate] of Object.entries(candidates)) {
  const usage = summary.terms[term]
  assert.equal(usage.showWhenUnmatched, candidate.showWhenUnmatched)
  assert.deepEqual(usage.unsupportedVariants, candidate.unsupportedVariants)
  assert.deepEqual(usage.variants.map(v => v.korean), candidate.variants)
  assert.deepEqual(sorted(Object.keys(usage.bySource)), sorted(Object.keys(config)))
  const seen = new Set()
  for (const variant of usage.variants) {
    const expectedIds = Object.keys(documents).filter(id => (documents[id].counts[term]?.[variant.korean] ?? 0) > 0)
    assert.deepEqual(sorted(variant.documents.map(d => d.id)), sorted(expectedIds), `Incomplete evidence: ${term}`)
    assert.equal(variant.documentCount, expectedIds.length)
    assert.equal(variant.occurrences, variant.documents.reduce((n, d) => n + d.occurrences, 0))
    assert.deepEqual(sorted(Object.keys(variant.bySource)), sorted(Object.keys(config)))
    for (const sid of Object.keys(config)) {
      assert.equal(variant.bySource[sid], states[sid] ? variant.documents.filter(d => d.source === sid).reduce((n, d) => n + d.occurrences, 0) : null)
    }
    for (const doc of variant.documents) {
      const original = documents[doc.id]
      assert.equal(doc.source, original.source)
      assert.equal(doc.path, original.path)
      assert.equal(doc.occurrences, original.counts[term][variant.korean])
      assert.deepEqual({ line: doc.line, endLine: doc.endLine, excerpt: doc.excerpt }, original.evidence[term][variant.korean])
      const source = summary.sources[doc.source]
      const url = new URL(doc.url)
      assert.equal(decodeURIComponent(url.pathname), decodeURIComponent(new URL(`${source.repository}/blob/${source.commit}/${doc.path}`).pathname))
      assert.equal(url.origin, 'https://github.com')
      assert.equal(url.hash, `#L${doc.line}-L${doc.endLine}`)
      seen.add(doc.id)
    }
  }
  assert.equal(usage.occurrences, usage.variants.reduce((n, v) => n + v.occurrences, 0))
  assert.equal(usage.documentCount, seen.size)
  for (const sid of Object.keys(config)) {
    assert.deepEqual(usage.bySource[sid], states[sid] ? {
      occurrences: usage.variants.reduce((n, v) => n + v.bySource[sid], 0),
      documentCount: [...seen].filter(id => documents[id].source === sid).length,
    } : { occurrences: null, documentCount: null })
  }
  assert.equal(usage.status, !usage.variants.length ? 'unsupported' : !hasCorpus ? 'not-collected' : usage.occurrences ? 'matched' : 'no-match')
}
console.log(`Usage validated: ${terms.length} terms, ${Object.keys(states).length}/${Object.keys(config).length} sources; ${summary.snapshotId.slice(0, 12)}`)
