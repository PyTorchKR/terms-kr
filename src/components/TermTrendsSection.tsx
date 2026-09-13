import React, { useState } from 'react'
import { Alert, Box, Button, Checkbox, FormControlLabel, Link, Typography } from '@mui/material'
import { useTermUsage } from '../hooks/useTermUsage'
import { TRENDS_LIMIT, trendsEmbedUrl, trendsExploreUrl } from '../utils/trendsEmbed'

export function TermTrendsSection({ term }: { term: string }): React.ReactNode {
  const { snapshot } = useTermUsage()
  const variants = snapshot?.terms[term]?.variants ?? []
  // Most used first, like the table above, so the default comparison covers the spellings that matter.
  const spellings = [...variants].sort((a, b) => b.occurrences - a.occurrences).map(variant => variant.korean)
  if (!spellings.length) return null
  return <TermTrendsContent key={`${term}:${spellings.join(',')}`} spellings={spellings} />
}

export function TermTrendsContent({ spellings }: { spellings: string[] }): React.ReactNode {
  const [selected, setSelected] = useState<string[]>(() => spellings.slice(0, TRENDS_LIMIT))
  const [reloads, setReloads] = useState(0)
  const query = { keywords: selected }
  const full = selected.length >= TRENDS_LIMIT

  const toggle = (spelling: string): void => setSelected(current => current.includes(spelling)
    ? current.filter(value => value !== spelling)
    : [...current, spelling].slice(0, TRENDS_LIMIT))

  return (
    <Box component="section" aria-labelledby="trends-heading" sx={{ mb: 5, borderTop: '2px solid var(--fg-1)', pt: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', mb: 1.5 }}>
        <Typography component="h2" id="trends-heading" sx={{ fontFamily: 'var(--ff-display)', fontSize: 24, fontWeight: 600 }}>
          표기별 검색 관심도
        </Typography>
        <Typography sx={{ color: 'var(--fg-3)', fontSize: 14 }}>Google Trends · 대한민국 · 최근 5년</Typography>
      </Box>
      <Typography sx={{ color: 'var(--fg-2)', fontSize: 14, mb: 2, maxWidth: 850 }}>
        문서 집계에 사용한 한국어 표기를 Google Trends에서 비교합니다. 검색 관심도는 번역의 정확성이나 표준 표기를 뜻하지 않으며, 일상적인 다른 의미의 검색도 함께 집계됩니다.
      </Typography>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        {spellings.map(spelling => (
          <FormControlLabel
            key={spelling}
            sx={{ m: 0, pl: 1, pr: 1.5, border: '1px solid var(--ptk-line-soft)', borderRadius: 1, bgcolor: selected.includes(spelling) ? 'var(--bg-3)' : 'transparent' }}
            control={<Checkbox
              size="small"
              checked={selected.includes(spelling)}
              disabled={full && !selected.includes(spelling)}
              onChange={() => toggle(spelling)}
            />}
            label={<Typography sx={{ fontSize: 14 }}>{spelling}</Typography>}
          />
        ))}
      </Box>
      <Typography sx={{ color: 'var(--fg-3)', fontSize: 13, mb: 2 }}>
        한 차트에서 최대 {TRENDS_LIMIT}개까지 비교합니다. 0~100은 선택한 표기끼리의 상대 관심도이며, 다른 차트의 값과는 비교할 수 없습니다.
      </Typography>

      {selected.length === 0 ? (
        <Alert severity="info" sx={{ mb: 2 }}>비교할 표기를 하나 이상 선택해 주세요.</Alert>
      ) : (
        <Box
          component="iframe"
          key={`${selected.join(',')}:${reloads}`}
          src={trendsEmbedUrl(query)}
          title={`${selected.join(', ')} 검색 관심도 비교`}
          loading="lazy"
          sx={{ width: '100%', height: 445, border: '1px solid var(--ptk-line-soft)', display: 'block', bgcolor: '#fff' }}
        />
      )}

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', mt: 1.5 }}>
        <Typography sx={{ color: 'var(--fg-3)', fontSize: 13, maxWidth: 620 }}>
          차트는 Google Trends에서 직접 불러옵니다. 빈 화면이나 접속 제한 메시지가 보이면 아래 링크로 확인해 주세요. 브라우저 보안 정책상 이 페이지는 차트 내부의 응답 상태를 판별할 수 없습니다.
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="text" onClick={() => setReloads(value => value + 1)} disabled={!selected.length}>차트 다시 불러오기</Button>
          <Link href={trendsExploreUrl(query)} target="_blank" rel="noopener noreferrer" sx={{ fontSize: 14, alignSelf: 'center' }}>
            Google Trends에서 비교 ↗
          </Link>
        </Box>
      </Box>
    </Box>
  )
}
