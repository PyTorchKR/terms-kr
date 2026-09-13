import React, { useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Typography,
  Button,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  IconButton,
  Snackbar,
  Breadcrumbs,
  Link,
  Skeleton,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import GitHubIcon from '@mui/icons-material/GitHub'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import HistoryIcon from '@mui/icons-material/History'
import AddIcon from '@mui/icons-material/Add'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { Layout } from '../components/Layout'
import { useTerms } from '../hooks/useTerms'
import type { TermMeaning, TermExample } from '../types/term'
import { getFeedbackUrl, getIssueUrl, getNewTermUrl } from '../data/const'
import { getReadableSourceUrl } from '../utils/sourceLinks'
import { TermUsageSection } from '../components/TermUsageSection'
import { TermTrendsSection } from '../components/TermTrendsSection'

function isTermExample(example: string | TermExample): example is TermExample {
  return typeof example === 'object' && 'en' in example && 'ko' in example
}

function MeaningContent({ meaning }: { meaning: TermMeaning }) {
  return (
    <Box>
      <Typography
        sx={{
          fontSize: 16,
          lineHeight: 1.7,
          color: 'var(--fg-1)',
          mb: 3,
        }}
      >
        {meaning.definition}
      </Typography>

      {meaning.examples.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Box
            sx={{
              fontFamily: 'var(--ff-mono)',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'var(--ptk-orange)',
              mb: 1.5,
            }}
          >
            예시
          </Box>
          <Box
            component="ul"
            sx={{
              listStyle: 'none',
              p: 0,
              m: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
            }}
          >
            {meaning.examples.map((example, exIndex) => (
              <Box
                key={exIndex}
                component="li"
                sx={{
                  bgcolor: 'var(--bg-3)',
                  borderLeft: '2px solid var(--ptk-orange)',
                  px: 2,
                  py: 1.5,
                  fontSize: 14,
                  lineHeight: 1.6,
                }}
              >
                {isTermExample(example) ? (
                  <>
                    <Box
                      sx={{
                        fontFamily: 'var(--ff-mono)',
                        fontSize: 11,
                        fontWeight: 700,
                        color: 'var(--fg-3)',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        mb: 0.5,
                      }}
                    >
                      EN
                    </Box>
                    <Box sx={{ color: 'var(--fg-2)', fontStyle: 'italic', mb: 1 }}>{example.en}</Box>
                    <Box
                      sx={{
                        fontFamily: 'var(--ff-mono)',
                        fontSize: 11,
                        fontWeight: 700,
                        color: 'var(--fg-3)',
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        mb: 0.5,
                      }}
                    >
                      KO
                    </Box>
                    <Box sx={{ color: 'var(--fg-1)' }}>{example.ko}</Box>
                    {example.source && (
                      <Link
                        href={getReadableSourceUrl(example.source)}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{
                          mt: 1,
                          display: 'inline-block',
                          fontFamily: 'var(--ff-mono)',
                          fontSize: 11,
                          letterSpacing: '0.04em',
                        }}
                      >
                        출처 →
                      </Link>
                    )}
                  </>
                ) : (
                  <Box sx={{ color: 'var(--fg-1)' }}>{example}</Box>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {meaning.synonyms.length > 0 && (
        <Box>
          <Box
            sx={{
              fontFamily: 'var(--ff-mono)',
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'var(--ptk-orange)',
              mb: 1.5,
            }}
          >
            유사 용어
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {meaning.synonyms.map((synonym, synIndex) => (
              <Box
                key={synIndex}
                sx={{
                  fontFamily: 'var(--ff-mono)',
                  fontSize: 12,
                  fontWeight: 600,
                  color: 'var(--fg-2)',
                  border: '1px solid var(--ptk-line-soft)',
                  bgcolor: '#fff',
                  px: 1.25,
                  py: 0.5,
                  letterSpacing: '0.02em',
                }}
              >
                {synonym}
              </Box>
            ))}
          </Box>
        </Box>
      )}
    </Box>
  )
}

export function TermDetailPage(): React.ReactNode {
  const { termId } = useParams<{ termId: string }>()
  const navigate = useNavigate()
  const { terms, loading, error } = useTerms()
  const [snackbarOpen, setSnackbarOpen] = useState(false)

  const term = useMemo(
    () => terms.find((t) => t.term === decodeURIComponent(termId || '')),
    [terms, termId]
  )

  const hasDuplicateKorean = useMemo(() => {
    if (!term) return false
    const koreanValues = term.meanings.map((m) => m.korean)
    return koreanValues.length !== new Set(koreanValues).size
  }, [term])

  if (loading) {
    return (
      <Layout>
        <Skeleton variant="text" width={200} height={24} sx={{ mb: 3 }} />
        <Skeleton variant="text" width={320} height={56} sx={{ mb: 3 }} />
        <Skeleton variant="rectangular" height={120} sx={{ mb: 2, borderRadius: 0 }} />
        <Skeleton variant="rectangular" height={120} sx={{ mb: 2, borderRadius: 0 }} />
      </Layout>
    )
  }

  if (error) {
    return <Layout><Alert severity="error">{error}</Alert></Layout>
  }

  if (!term) {
    return (
      <Layout>
        <Alert severity="warning">용어를 찾을 수 없습니다</Alert>
        <Button onClick={() => navigate('/')} sx={{ mt: 2 }}>
          뒤로 가기
        </Button>
      </Layout>
    )
  }

  const handleGoBack = (): void => {
    navigate('/')
  }

  const handleOpenFeedback = (): void => {
    window.open(getFeedbackUrl(term.term), '_blank', 'noopener,noreferrer')
  }

  const handleRequestMeaning = (): void => {
    window.open(getNewTermUrl(term.term), '_blank', 'noopener,noreferrer')
  }

  const handleCopyKorean = (korean: string): void => {
    navigator.clipboard.writeText(korean).then(() => {
      setSnackbarOpen(true)
    }).catch(() => {})
  }

  return (
    <Layout>
      <Breadcrumbs
        sx={{
          mb: 4,
          fontFamily: 'var(--ff-mono)',
          fontSize: 12,
          letterSpacing: '0.04em',
          '& .MuiBreadcrumbs-separator': { color: 'var(--ptk-line)' },
        }}
      >
        <Link
          component="button"
          onClick={handleGoBack}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 0.5,
            cursor: 'pointer',
            color: 'var(--fg-3)',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            letterSpacing: 'inherit',
            textTransform: 'uppercase',
            border: 0,
            background: 'transparent',
            p: 0,
            '&:hover': { color: 'var(--ptk-orange)' },
          }}
          underline="hover"
        >
          ← 목록으로
        </Link>
        <Box
          component="span"
          sx={{
            color: 'var(--fg-1)',
            fontWeight: 700,
            textTransform: 'uppercase',
          }}
        >
          {term.term}
        </Box>
      </Breadcrumbs>

      <Box
        sx={{
          pb: 3,
          mb: 4,
          borderBottom: '2px solid var(--fg-1)',
        }}
      >
        <Box
          sx={{
            fontFamily: 'var(--ff-mono)',
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: 'var(--ptk-orange)',
            mb: 1.5,
          }}
        >
          용어
        </Box>
        <Typography
          component="h1"
          sx={{
            fontFamily: 'var(--ff-display)',
            fontWeight: 700,
            fontSize: 'clamp(36px, 5vw, 56px)',
            lineHeight: 1.05,
            letterSpacing: '-0.02em',
            color: 'var(--fg-1)',
            wordBreak: 'break-word',
          }}
        >
          {term.term}
        </Typography>
        {term.meanings.length > 1 && (
          <Box
            sx={{
              mt: 2,
              fontFamily: 'var(--ff-mono)',
              fontSize: 13,
              color: 'var(--ptk-purple)',
              letterSpacing: '0.04em',
            }}
          >
            {term.meanings.length}개의 의미가 등록되어 있습니다
          </Box>
        )}
      </Box>

      {term.notes && (
        <Alert
          icon={<InfoOutlinedIcon />}
          severity="success"
          sx={{ mb: 3 }}
        >
          <Typography sx={{ fontWeight: 700, mb: 0.5, fontSize: 14 }}>
            번역 참고사항
          </Typography>
          <Typography sx={{ fontSize: 14, color: 'var(--fg-2)' }}>{term.notes}</Typography>
        </Alert>
      )}

      {term.issueNumber && (
        <Box
          sx={{
            mb: 3,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            fontFamily: 'var(--ff-mono)',
            fontSize: 12,
            color: 'var(--fg-3)',
            letterSpacing: '0.02em',
          }}
        >
          <HistoryIcon fontSize="small" sx={{ color: 'var(--fg-3)' }} />
          <Link
            href={getIssueUrl(term.issueNumber)}
            target="_blank"
            rel="noopener noreferrer"
            sx={{ fontFamily: 'inherit', fontSize: 'inherit' }}
          >
            논의 내역 보기 #{term.issueNumber}
          </Link>
        </Box>
      )}

      <Box sx={{ mb: 5 }}>
        {term.meanings.length === 1 ? (
          <SenseBlock
            index={1}
            meaning={term.meanings[0]}
            onCopy={handleCopyKorean}
          />
        ) : (
          term.meanings.map((meaning, index) => (
            <Accordion key={index} defaultExpanded={index === 0} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                  <Box
                    sx={{
                      fontFamily: 'var(--ff-display)',
                      fontWeight: 700,
                      fontSize: 22,
                      color: 'var(--ptk-orange)',
                      lineHeight: 1,
                      minWidth: 28,
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography
                      sx={{
                        fontFamily: 'var(--ff-display)',
                        fontWeight: 700,
                        fontSize: 20,
                        letterSpacing: '-0.005em',
                        color: 'var(--fg-1)',
                      }}
                    >
                      {meaning.korean}
                    </Typography>
                    {hasDuplicateKorean && (
                      <Typography
                        sx={{
                          mt: 0.25,
                          fontSize: 13,
                          color: 'var(--fg-3)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: { xs: 200, sm: 400 },
                        }}
                      >
                        {meaning.definition.slice(0, 60)}{meaning.definition.length > 60 ? '...' : ''}
                      </Typography>
                    )}
                  </Box>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleCopyKorean(meaning.korean)
                    }}
                    aria-label={`${meaning.korean} 복사`}
                    sx={{ color: 'var(--fg-3)', '&:hover': { color: 'var(--ptk-orange)' } }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ pl: { xs: 2.5, md: 7 } }}>
                <MeaningContent meaning={meaning} />
              </AccordionDetails>
            </Accordion>
          ))
        )}
      </Box>

      <TermUsageSection term={term.term} />

      <TermTrendsSection term={term.term} />

      <Box
        sx={{
          mt: 6,
          pt: 4,
          borderTop: '1px solid var(--ptk-line-soft)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: 1.5,
        }}
      >
        <Button variant="contained" startIcon={<GitHubIcon />} onClick={handleOpenFeedback}>
          번역 개선 제안
        </Button>
        <Button variant="outlined" startIcon={<AddIcon />} onClick={handleRequestMeaning}>
          새로운 의미 추가 요청
        </Button>
        <Button
          variant="text"
          startIcon={<ArrowBackIcon />}
          onClick={handleGoBack}
          sx={{ ml: { sm: 'auto' } }}
        >
          목록으로 돌아가기
        </Button>
      </Box>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={() => setSnackbarOpen(false)}
        message="번역이 복사되었습니다"
      />
    </Layout>
  )
}

interface SenseBlockProps {
  index: number
  meaning: TermMeaning
  onCopy: (korean: string) => void
}

function SenseBlock({ index, meaning, onCopy }: SenseBlockProps) {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '56px 1fr' },
        gap: { xs: 2, md: 3 },
        border: '1px solid var(--ptk-line-soft)',
        p: { xs: 2.5, md: 3.5 },
        bgcolor: '#fff',
      }}
    >
      <Box
        sx={{
          fontFamily: 'var(--ff-display)',
          fontWeight: 700,
          fontSize: 36,
          color: 'var(--ptk-orange)',
          lineHeight: 1,
        }}
      >
        {index}
      </Box>
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <Typography
            sx={{
              flex: 1,
              fontFamily: 'var(--ff-display)',
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: '-0.01em',
              color: 'var(--fg-1)',
            }}
          >
            {meaning.korean}
          </Typography>
          <IconButton
            size="small"
            onClick={() => onCopy(meaning.korean)}
            aria-label={`${meaning.korean} 복사`}
            sx={{ color: 'var(--fg-3)', '&:hover': { color: 'var(--ptk-orange)' } }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Box>
        <MeaningContent meaning={meaning} />
      </Box>
    </Box>
  )
}
