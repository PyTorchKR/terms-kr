import React, { useMemo, useState } from 'react'
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, FormControl,
  InputLabel, Link, MenuItem, Select, Skeleton, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Typography,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { useTermUsage } from '../hooks/useTermUsage'
import { getUsageCommunities } from '../utils/usageCommunities'
import type { TermUsage, UsageSnapshot } from '../types/usage'

const number = (value: number): string => value.toLocaleString('ko-KR')
const formatDate = (value: string | null): string => value
  ? new Intl.DateTimeFormat('ko-KR', { timeZone: 'Asia/Seoul', dateStyle: 'medium' }).format(new Date(value)) : '미수집'
const cell = { fontSize: 14, borderColor: 'var(--ptk-line-soft)', py: 1.5 }

export function TermUsageSection({ term }: { term: string }): React.ReactNode {
  const { snapshot, error } = useTermUsage()
  if (error) return <Alert severity="info" sx={{ my: 3 }}>{error}</Alert>
  if (!snapshot) return <Skeleton aria-label="번역 표기 통계 불러오는 중" variant="rectangular" height={100} sx={{ mb: 4 }} />
  const usage = snapshot.terms[term]
  if (!usage) return <Alert severity="info">이 용어는 현재 통계 스냅샷에 포함되어 있지 않습니다.</Alert>
  // Absence of a match is not a fabricated statistic for upstream-only terms.
  if (!usage.showWhenUnmatched && usage.status !== 'matched') return null
  return <TermUsageContent key={`${term}:${snapshot.snapshotId}`} usage={usage} snapshot={snapshot} />
}

export function TermUsageContent({ usage, snapshot }: { usage: TermUsage; snapshot: UsageSnapshot }): React.ReactNode {
  const sourceIds = Object.keys(snapshot.sources)
  const sourceLabels = Object.fromEntries(sourceIds.map(id => [id, snapshot.sources[id].label]))
  const communities = getUsageCommunities(snapshot.sources, usage.bySource).join(' · ')
  const [variant, setVariant] = useState('')
  const [showAll, setShowAll] = useState(false)
  const evidence = useMemo(() => usage.variants
    .filter(v => !variant || v.korean === variant)
    .flatMap(v => v.documents.map(doc => ({ ...doc, korean: v.korean })))
    .sort((a, b) => b.occurrences - a.occurrences || a.id.localeCompare(b.id)), [usage, variant])
  const included = Object.values(snapshot.corpus).reduce((sum, item) => sum + (item.included ?? 0), 0)
  const scanned = Object.values(snapshot.corpus).reduce((sum, item) => sum + (item.scanned ?? 0), 0)
  const date = formatDate(snapshot.generatedAt)
  const visible = showAll ? evidence : evidence.slice(0, 8)

  return (
    <Box component="section" aria-labelledby="usage-heading" sx={{ mt: 5, mb: 5, borderTop: '2px solid var(--fg-1)', pt: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', mb: 1.5 }}>
        <Typography component="h2" id="usage-heading" sx={{ fontFamily: 'var(--ff-display)', fontSize: 24, fontWeight: 600 }}>
          번역 문서에서의 쓰임
        </Typography>
        {communities && <Typography sx={{ color: 'var(--ptk-orange-press)', fontSize: 14, fontWeight: 700 }}>{communities}</Typography>}
      </Box>
      <Typography sx={{ color: 'var(--fg-2)', fontSize: 14, mb: 3, maxWidth: 850 }}>
        한국어 번역 문서에 아래 표기가 나타난 횟수입니다. 특정 영문 용어의 번역 횟수나 권장 번역을 뜻하지 않으며, 다의어와 다른 단어 안의 출현도 포함될 수 있습니다.
      </Typography>

      <Box component="dl" sx={{ m: 0, mb: 3, p: 2.5, bgcolor: 'var(--bg-3)', display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: '1fr 1fr 1.4fr' }, gap: 3 }}>
        {[
          { label: '표기 출현', value: usage.status === 'unsupported' ? '집계 제외' : usage.status === 'not-collected' ? '집계 대상 없음' : `${number(usage.occurrences)}회` },
          { label: '출현 문서', value: usage.status === 'not-collected' ? '—' : `${number(usage.documentCount)}개` },
          { label: '최근 집계 · 한국 시간', value: date },
        ].map(item => (
          <Box key={item.label}>
            <Typography component="dt" sx={{ color: 'var(--fg-3)', fontSize: 14, mb: 1 }}>{item.label}</Typography>
            <Typography component="dd" sx={{ m: 0, fontFamily: 'var(--ff-display)', fontSize: { xs: 22, sm: 26 }, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{item.value}</Typography>
          </Box>
        ))}
      </Box>

      {usage.status === 'no-match' && (
        <Typography sx={{ fontSize: 14, color: 'var(--fg-2)', mb: 2 }}>
          이번 집계 범위에서는 등록된 한글 표기를 찾지 못했습니다. 초안 제외·띄어쓰기 차이·영문 그대로의 사용 등은 이 숫자에 반영되지 않습니다.
        </Typography>
      )}
      {usage.status === 'not-collected' && <Typography sx={{ fontSize: 14, mb: 2 }}>아직 집계한 한국어 문서가 없거나, 확인한 문서가 모두 제외되었습니다. 0회라는 의미는 아닙니다.</Typography>}
      {usage.variants.length > 0 && (
        <TableContainer tabIndex={0} aria-label="표기별 출현 수, 작은 화면에서는 가로로 스크롤할 수 있습니다" sx={{ mb: 1, border: '1px solid var(--ptk-line-soft)', '&:focus-visible': { outline: '2px solid var(--ptk-orange)' } }}>
          <Table size="small" sx={{ minWidth: 610 }}>
            <caption style={{ captionSide: 'bottom', fontSize: 14, padding: 16, color: 'var(--fg-3)' }}>
              같은 용어 안에서 겹치는 표기는 왼쪽부터, 같은 위치에서는 긴 표기를 먼저 셉니다. 문서 수는 행끼리 더하지 않습니다. ‘—’는 미수집이며, 전체는 집계된 출처만의 합계입니다.
            </caption>
            <TableHead sx={{ bgcolor: 'var(--bg-3)' }}>
              <TableRow>
                <TableCell sx={{ ...cell, fontWeight: 700 }}>한글 표기</TableCell>
                <TableCell align="right" sx={{ ...cell, fontWeight: 700 }}>전체</TableCell>
                {sourceIds.map(source => <TableCell key={source} align="right" sx={cell}>{sourceLabels[source]}</TableCell>)}
                <TableCell align="right" sx={cell}>문서</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[...usage.variants].sort((a, b) => b.occurrences - a.occurrences).map(row => (
                <TableRow key={row.korean}>
                  <TableCell component="th" scope="row" sx={{ ...cell, fontWeight: 600 }}>{row.korean}</TableCell>
                  <TableCell align="right" sx={{ ...cell, fontWeight: 700, color: row.occurrences ? 'var(--ptk-orange-press)' : 'var(--fg-3)', fontVariantNumeric: 'tabular-nums' }}>{usage.status === 'not-collected' ? '—' : `${number(row.occurrences)}회`}</TableCell>
                  {sourceIds.map(source => <TableCell key={source} align="right" sx={{ ...cell, fontVariantNumeric: 'tabular-nums' }}>{row.bySource[source] == null ? '—' : number(row.bySource[source])}</TableCell>)}
                  <TableCell align="right" sx={cell}>{usage.status === 'not-collected' ? '—' : `${number(row.documentCount)}개`}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      {usage.unsupportedVariants.length > 0 && <Typography sx={{ fontSize: 14, color: 'var(--fg-3)', my: 2 }}>영문·약어 표기 집계 제외: {usage.unsupportedVariants.join(', ')}. 0회라는 의미는 아닙니다.</Typography>}

      {evidence.length > 0 || usage.occurrences > 0 ? (
        <Accordion sx={{ mt: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="usage-evidence-content" id="usage-evidence-header">
            <Typography sx={{ fontSize: 16, fontWeight: 600 }}>문서별 근거 확인</Typography>
          </AccordionSummary>
          <AccordionDetails id="usage-evidence-content">
            <Typography sx={{ fontSize: 14, color: 'var(--fg-3)', mb: 2 }}>표기·문서마다 첫 출현 문맥을 보여줍니다. 출처는 집계한 커밋의 해당 문단으로 연결됩니다.</Typography>
            <FormControl size="small" sx={{ minWidth: 180, mb: 2 }}>
              <InputLabel id="usage-variant-label">한글 표기</InputLabel>
              <Select labelId="usage-variant-label" label="한글 표기" value={variant} onChange={event => { setVariant(event.target.value); setShowAll(false) }}>
                <MenuItem value="">모든 표기</MenuItem>
                {usage.variants.filter(v => v.occurrences > 0).map(v => <MenuItem key={v.korean} value={v.korean}>{v.korean}</MenuItem>)}
              </Select>
            </FormControl>
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {visible.map(row => (
                <Box component="li" key={`${row.id}:${row.korean}`} sx={{ py: 2, borderTop: '1px solid var(--ptk-line-soft)' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2, mb: 1 }}>
                    <Typography sx={{ fontSize: 14, fontWeight: 700 }}>{row.korean} · {sourceLabels[row.source]}</Typography>
                    <Typography sx={{ fontSize: 14, whiteSpace: 'nowrap' }}>문서 내 {number(row.occurrences)}회</Typography>
                  </Box>
                  <Link href={row.url} target="_blank" rel="noopener noreferrer" sx={{ fontSize: 14, overflowWrap: 'anywhere' }}>{row.path} ↗</Link>
                  <Typography sx={{ mt: 1, fontSize: 14, color: 'var(--fg-2)', lineHeight: 1.7, overflowWrap: 'anywhere' }}>…{row.excerpt}…</Typography>
                </Box>
              ))}
            </Box>
            {evidence.length > 8 && <Button variant="text" onClick={() => setShowAll(!showAll)}>{showAll ? '간단히 보기' : `근거 ${number(evidence.length)}건 모두 보기`}</Button>}
          </AccordionDetails>
        </Accordion>
      ) : null}

      <Accordion sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="usage-method-content" id="usage-method-header">
          <Typography sx={{ fontSize: 16, fontWeight: 600 }}>집계 범위와 기준</Typography>
        </AccordionSummary>
        <AccordionDetails id="usage-method-content">
          <Typography sx={{ fontSize: 14, mb: 1.5 }}>
            출처별 고정 커밋을 기준으로 확인한 {number(scanned)}개 문서 중 포함 조건을 만족하는 {number(included)}개가 대상입니다. 출처마다 기준 시점이 다를 수 있으며, 최신 원격 문서 전체를 뜻하지 않습니다.
          </Typography>
          <Box component="ul" sx={{ pl: 2.5, fontSize: 14, lineHeight: 1.8, color: 'var(--fg-2)' }}>
            {sourceIds.map(source => <li key={source}>{sourceLabels[source]}: {snapshot.sources[source].status === 'not-collected' ? '미수집' : <>{snapshot.corpus[source].included}개 / 확인한 문서 {snapshot.corpus[source].scanned}개 · 집계 {formatDate(snapshot.sources[source].generatedAt)} · <Link href={`${snapshot.sources[source].repository}/tree/${snapshot.sources[source].commit}`} target="_blank" rel="noopener noreferrer">{snapshot.sources[source].commit?.slice(0, 8)}</Link></>}</li>)}
            <li>제목·문단·목록·표·인용문 포함. 코드·주석·메타데이터·URL·이미지·raw HTML 블록 제외.</li>
            <li>NFC 정규화·소문자화·연속 공백 축약 후 부분 문자열 검색. 띄어쓰기는 임의로 합치지 않습니다.</li>
            <li>사전의 번역·유사 용어와 별도로 관리하는 토론 후보 표기를 검색합니다. 토론 후보는 사전의 권장 번역이 아닙니다.</li>
            <li>문서 간 영문 대응 확인은 포함 범위를 정하기 위한 것이며 문장별 번역 정렬은 아닙니다. 일반 Markdown은 대응 경로, KREW 블로그는 원문·번역 고지·초안 여부를 확인합니다.</li>
            <li>출현 근거가 없는 용어는 별도로 추적하는 후보를 제외하고 통계 영역을 숨깁니다. 사전의 대표 번역이나 의미 순서는 바꾸지 않습니다.</li>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            <Link href={`${import.meta.env.BASE_URL}usage/scanned.md`} download sx={{ fontSize: 14 }}>스캔 문서 목록 받기</Link>
            <Link href={`${import.meta.env.BASE_URL}usage/term-usage.json`} download sx={{ fontSize: 14 }}>통계 JSON 받기</Link>
          </Box>
          <Typography sx={{ mt: 2, fontSize: 12, color: 'var(--fg-3)', overflowWrap: 'anywhere' }}>규칙 {snapshot.countingRuleVersion} · 스냅샷 {snapshot.snapshotId.slice(0, 12)}</Typography>
        </AccordionDetails>
      </Accordion>
    </Box>
  )
}
