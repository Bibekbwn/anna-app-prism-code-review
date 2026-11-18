'use client'

import { useState } from 'react'
import type { ReviewHistoryEntry, ReviewReport } from './data'
import type { LocalPrismApi } from './use-local-prism'

export function usePrismReview(api: LocalPrismApi, effort: string, setEffort: (value: string) => void, onNotice: (message: string) => void, onComplete: () => void) {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('Auto-detect')
  const [report, setReport] = useState<ReviewReport | null>(null)
  const [isReviewing, setIsReviewing] = useState(false)

  async function startReview() {
    if (!code.trim()) {
      onNotice('Add code before starting a review.')
      return
    }
    if (code.length > 40000) {
      onNotice('Keep code under 40,000 characters per review.')
      return
    }

    let backendStatus = api.status
    if (!backendStatus) {
      try {
        backendStatus = await api.connect()
      } catch (error) {
        onNotice(error instanceof Error ? error.message : 'Local PRISM companion is unavailable.')
        return
      }
    }

    setIsReviewing(true)
    try {
      const result = await api.request<{ report: ReviewHistoryEntry; ai: { configured: boolean; failure?: { reason: string; provider?: string } | null } }>(
        'reviews',
        { method: 'POST', body: JSON.stringify({ code, language, effort }) },
      )
      const entry = result.report
      setReport(entry.report)
      setLanguage(entry.language)
      setEffort(entry.effort)
      await api.refreshHistory()
      onComplete()

      if (result.ai.failure?.reason === 'no_key') {
        onNotice('Regex review completed. Set a provider key locally to enable AI agents.')
      } else if (result.ai.failure?.reason === 'no_sdk') {
        onNotice('Regex review completed. Install the local SDK for your configured AI provider.')
      } else {
        onNotice(result.ai.configured && entry.effort !== 'Lite' ? 'PRISM regex and AI review completed.' : 'PRISM regex review completed.')
      }
    } catch (error) {
      onNotice(error instanceof Error ? error.message : 'PRISM could not complete this review.')
    } finally {
      setIsReviewing(false)
    }
  }

  function openHistoryEntry(entry: ReviewHistoryEntry) {
    setReport(entry.report)
    setLanguage(entry.language)
    setEffort(entry.effort)
  }

  return { code, setCode, language, setLanguage, report, setReport, isReviewing, startReview, openHistoryEntry }
}
