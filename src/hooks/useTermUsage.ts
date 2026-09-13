import { useEffect, useState } from 'react'
import type { UsageSnapshot } from '../types/usage'

let cached: Promise<UsageSnapshot> | undefined

function loadUsage(): Promise<UsageSnapshot> {
  if (!cached) {
    cached = fetch(`${import.meta.env.BASE_URL}usage/term-usage.json`)
      .then(async (response) => {
        if (!response.ok) throw new Error('통계 파일을 불러오지 못했습니다.')
        const value = await response.json() as UsageSnapshot
        if (value.schemaVersion !== 2 || !value.snapshotId || !value.terms || !value.corpus || !value.sources) {
          throw new Error('통계 파일의 형식을 확인할 수 없습니다.')
        }
        return value
      })
      .catch((error: unknown) => {
        cached = undefined
        throw error
      })
  }
  return cached
}

// Invoked only by the detail page; search/cards keep their original data flow.
export function useTermUsage(): { snapshot: UsageSnapshot | null; error: string | null } {
  const [snapshot, setSnapshot] = useState<UsageSnapshot | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    let active = true
    loadUsage().then(
      value => { if (active) setSnapshot(value) },
      () => { if (active) setError('통계를 불러오지 못했습니다. 페이지를 새로고침해 주세요. 용어와 번역은 계속 볼 수 있습니다.') },
    )
    return () => { active = false }
  }, [])
  return { snapshot, error }
}
