import type { TermUsage, UsageSnapshot } from '../types/usage'

export function getUsageCommunities(
  sources: UsageSnapshot['sources'],
  bySource: TermUsage['bySource'],
): string[] {
  return [...new Set(Object.entries(sources)
    .filter(([id, source]) => source.status === 'collected' && (bySource[id]?.documentCount ?? 0) > 0)
    .map(([, source]) => source.community))]
}
