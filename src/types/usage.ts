export interface UsageDocument {
  id: string
  source: string
  path: string
  occurrences: number
  url: string
  line: number
  endLine: number
  excerpt: string
}

export interface UsageVariant {
  korean: string
  occurrences: number
  documentCount: number
  bySource: Record<string, number | null>
  documents: UsageDocument[]
}

export interface TermUsage {
  showWhenUnmatched: boolean
  status: 'matched' | 'no-match' | 'unsupported' | 'not-collected'
  occurrences: number
  documentCount: number
  bySource: Record<string, { occurrences: number | null; documentCount: number | null }>
  variants: UsageVariant[]
  unsupportedVariants: string[]
}

export interface UsageSnapshot {
  schemaVersion: 2
  snapshotId: string
  countingRuleVersion: string
  generatedAt: string | null
  candidateHash: string
  sources: Record<string, {
    repository: string
    label: string
    community: string
    status: 'collected' | 'not-collected'
    commit: string | null
    generatedAt: string | null
    snapshotId: string | null
  }>
  corpus: Record<string, { scanned: number | null; included: number | null }>
  terms: Record<string, TermUsage>
}
