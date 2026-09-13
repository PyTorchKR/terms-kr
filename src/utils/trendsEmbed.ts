// Google Trends compares at most five search terms in one chart.
export const TRENDS_LIMIT = 5
export const TRENDS_GEO = 'KR'
export const TRENDS_TIME = 'today 5-y'

export interface TrendsQuery {
  keywords: string[]
  geo?: string
  time?: string
  timezone?: number
}

function repeated(value: string, count: number): string {
  return Array.from({ length: count }, () => value).join(',')
}

/** The comparison Google Trends itself uses for the explore link and the embed. */
export function trendsCompareQuery({ keywords, geo = TRENDS_GEO, time = TRENDS_TIME }: TrendsQuery): string {
  return `date=${repeated(time, keywords.length)}&geo=${repeated(geo, keywords.length)}&q=${keywords.join(',')}&hl=ko`
}

export function trendsEmbedUrl(query: TrendsQuery): string {
  const { keywords, geo = TRENDS_GEO, time = TRENDS_TIME, timezone = new Date().getTimezoneOffset() } = query
  const request = {
    comparisonItem: keywords.map(keyword => ({ keyword, geo, time })),
    category: 0,
    property: '',
  }
  const parameters = [
    'hl=ko',
    `tz=${timezone}`,
    `req=${encodeURIComponent(JSON.stringify(request))}`,
    `eq=${encodeURIComponent(trendsCompareQuery(query))}`,
  ]
  return `https://trends.google.com/trends/embed/explore/TIMESERIES?${parameters.join('&')}`
}

export function trendsExploreUrl(query: TrendsQuery): string {
  const { keywords, geo = TRENDS_GEO, time = TRENDS_TIME } = query
  const parameters = new URLSearchParams({
    date: repeated(time, keywords.length),
    geo: repeated(geo, keywords.length),
    q: keywords.join(','),
    hl: 'ko',
  })
  return `https://trends.google.com/trends/explore?${parameters.toString()}`
}
