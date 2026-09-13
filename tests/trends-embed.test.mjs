import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import ts from 'typescript'

const source = readFileSync(new URL('../src/utils/trendsEmbed.ts', import.meta.url), 'utf8')
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText
const { TRENDS_LIMIT, trendsCompareQuery, trendsEmbedUrl, trendsExploreUrl } = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)

const query = { keywords: ['미세 조정', '파인튜닝'], timezone: -540 }

test('the embed request carries one comparison item per spelling', () => {
  const url = new URL(trendsEmbedUrl(query))
  assert.equal(url.origin + url.pathname, 'https://trends.google.com/trends/embed/explore/TIMESERIES')
  assert.equal(url.searchParams.get('tz'), '-540')
  assert.equal(url.searchParams.get('hl'), 'ko')
  assert.deepEqual(JSON.parse(url.searchParams.get('req')), {
    comparisonItem: [
      { keyword: '미세 조정', geo: 'KR', time: 'today 5-y' },
      { keyword: '파인튜닝', geo: 'KR', time: 'today 5-y' },
    ],
    category: 0,
    property: '',
  })
  assert.equal(url.searchParams.get('eq'), 'date=today 5-y,today 5-y&geo=KR,KR&q=미세 조정,파인튜닝&hl=ko')
})

test('the explore link opens the same comparison', () => {
  const url = new URL(trendsExploreUrl(query))
  assert.equal(url.origin + url.pathname, 'https://trends.google.com/trends/explore')
  assert.equal(url.searchParams.get('q'), '미세 조정,파인튜닝')
  assert.equal(url.searchParams.get('date'), 'today 5-y,today 5-y')
  assert.equal(url.searchParams.get('geo'), 'KR,KR')
  // Spaces must survive encoding; a raw space would break the link.
  assert.ok(!url.search.includes(' '))
})

test('a single spelling is not padded and the limit stays at five', () => {
  assert.equal(trendsCompareQuery({ keywords: ['텐서'] }), 'date=today 5-y&geo=KR&q=텐서&hl=ko')
  assert.equal(TRENDS_LIMIT, 5)
})
