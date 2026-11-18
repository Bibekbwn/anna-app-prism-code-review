'use client'

import { useEffect, useState } from 'react'
import { PrismHeader } from './prism-header'
import { PrismPageContent } from './prism-page-content'
import { pages, sampleCode, type PageId, type ReviewHistoryEntry } from './data'
import { useAnnaRuntime } from './anna-runtime'
import { useLocalPrismApi } from './use-local-prism'
import { usePrismCollections } from './use-prism-collections'
import { usePrismPreferences } from './use-prism-preferences'
import { usePrismReview } from './use-prism-review'

export function PrismApp() {
  const [activePage, setActivePage] = useState<PageId>('new')
  const [notice, setNotice] = useState('')
  const api = useLocalPrismApi()
  const preferences = usePrismPreferences(api, setNotice)
  const review = usePrismReview(
    api,
    preferences.effort,
    (value) => preferences.setEffort(value),
    setNotice,
    () => setActivePage('results'),
  )
  const collections = usePrismCollections(api, setNotice)
  const pageLabel = pages.find((page) => page.id === activePage)?.label ?? 'New Review'

  useAnnaRuntime(pageLabel)

  useEffect(() => {
    if (!notice) return
    const timeout = window.setTimeout(() => setNotice(''), 3000)
    return () => window.clearTimeout(timeout)
  }, [notice])

  function navigate(page: PageId) {
    setActivePage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function connect() {
    try {
      const status = await api.connect()
      const message = status.ai.configured
        ? `PRISM ${status.version} connected with ${status.ai.provider} AI.`
        : `PRISM ${status.version} connected in regex-only mode. Configure a local AI provider to enable AI agents.`
      setNotice(message)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Local PRISM companion is unavailable.')
    }
  }

  function openHistoryEntry(entry: ReviewHistoryEntry) {
    review.openHistoryEntry(entry)
    navigate('results')
  }

  return (
    <div className={`prism-shell${preferences.theme === 'Light' ? ' theme-light' : ''}`}>
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <PrismHeader activePage={activePage} onNavigate={navigate} />
      <main className="page-content" id="main-content" tabIndex={-1}>
        <PrismPageContent
          activePage={activePage}
          newReview={{
            code: review.code,
            setCode: review.setCode,
            language: review.language,
            setLanguage: review.setLanguage,
            effort: preferences.effort,
            setEffort: (value) => preferences.setEffort(value),
            connectionStatus: api.connectionStatus,
            aiConfigured: Boolean(api.status?.ai.configured),
            aiProvider: api.status?.ai.provider ?? '',
            isReviewing: review.isReviewing,
            onConnect: connect,
            onLoadSample: () => review.setCode(sampleCode),
            onReview: review.startReview,
          }}
          results={{
            report: review.report,
            language: review.language,
            effort: preferences.effort,
            showSuggestions: preferences.suggestions,
            onNewReview: () => navigate('new'),
            onExport: () => collections.exportReport(review.report),
          }}
          history={{
            entries: collections.history,
            onOpen: openHistoryEntry,
            onNewReview: () => navigate('new'),
            onExport: collections.exportHistory,
            onClear: collections.clearHistory,
          }}
          templates={{
            customTemplates: collections.customTemplates,
            onUseTemplate: (code) => {
              review.setCode(code)
              navigate('new')
              setNotice('Template loaded into the editor.')
            },
            onCreateTemplate: collections.createTemplate,
            onDeleteTemplate: collections.deleteTemplate,
            onToast: setNotice,
          }}
          compare={{ onToast: setNotice }}
          preferences={{
            effort: preferences.effort,
            setEffort: (value) => preferences.setEffort(value),
            theme: preferences.theme,
            setTheme: (value) => preferences.setTheme(value),
            suggestions: preferences.suggestions,
            setSuggestions: (value) => preferences.setSuggestions(value),
            localUrl: api.localUrl,
            setLocalUrl: api.setLocalUrl,
            connectionStatus: api.connectionStatus,
            backendStatus: api.status,
            onConnect: connect,
            onSave: preferences.save,
            onReset: preferences.reset,
          }}
        />
      </main>
      {notice && <div className="toast" role="status">{notice}</div>}
    </div>
  )
}
