import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const source = readFileSync(new URL('../src/utils/usageCommunities.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText
const { getUsageCommunities } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)
const sources = {
  transformers: { community: 'Hugging Face KREW', status: 'collected' },
  blog: { community: 'Hugging Face KREW', status: 'collected' },
  pytorch: { community: 'PyTorch', status: 'collected' },
  pending: { community: 'Pending community', status: 'not-collected' },
}
const found = { occurrences: 2, documentCount: 1 }
const absent = { occurrences: 0, documentCount: 0 }

test('only communities with term evidence are shown, without duplicates', () => {
  assert.deepEqual(getUsageCommunities(sources, { transformers: found, blog: found, pytorch: absent }), ['Hugging Face KREW'])
  assert.deepEqual(getUsageCommunities(sources, { transformers: absent, pytorch: found }), ['PyTorch'])
  assert.deepEqual(getUsageCommunities(sources, { transformers: found, pytorch: found }), ['Hugging Face KREW', 'PyTorch'])
  assert.deepEqual(getUsageCommunities(sources, { transformers: absent, pending: { occurrences: null, documentCount: null } }), [])
})
