import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

// Compile the small TypeScript helper in memory; no new runner/dependency needed.
const source = readFileSync(new URL('../src/utils/sourceLinks.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText
const { getReadableSourceUrl } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)

test('HF Markdown examples link to the corresponding language and Docs page', () => {
  assert.equal(getReadableSourceUrl('https://github.com/huggingface/transformers/blob/abc/docs/source/ko/perplexity.md#L13-L28'), 'https://huggingface.co/docs/transformers/ko/perplexity')
  assert.equal(getReadableSourceUrl('https://github.com/huggingface/smolagents/blob/main/docs/source/ko/examples/rag.md'), 'https://huggingface.co/docs/smolagents/ko/examples/rag')
  assert.equal(getReadableSourceUrl('https://github.com/huggingface/smolagents/blob/main/docs/source/en/index.md'), 'https://huggingface.co/docs/smolagents/en/index')
})
test('blog translations link to the KREW article, not unrelated library docs', () => {
  assert.equal(getReadableSourceUrl('https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/blob/aa3c6450bea58167f12a5ca42cffa7193f1819fa/_posts/2025-09-26-Introducing-smolagents.md'), 'https://hugging-face-krew.github.io/Introducing-smolagents/')
  assert.equal(getReadableSourceUrl('https://github.com/Hugging-Face-KREW/hugging-face-krew.github.io/blob/main/_posts/2025-11-3-Welcome-GPT-OSS.md'), 'https://hugging-face-krew.github.io/Welcome-GPT-OSS/')
})
test('unrelated sources, already-readable links, and invalid URLs stay unchanged', () => {
  for (const url of ['https://github.com/pytorch/pytorch', 'https://huggingface.co/docs/smolagents/ko/index', 'https://www.deeplearningbook.org/', 'invalid']) assert.equal(getReadableSourceUrl(url), url)
})
