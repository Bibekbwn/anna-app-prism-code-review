'use client'

import type { ReviewReport, SnippetTemplate } from './data'
import type { LocalPrismApi } from './use-local-prism'

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function usePrismCollections(api: LocalPrismApi, onNotice: (message: string) => void) {
  async function ensureConnected() {
    if (api.ready) return true
    try {
      await api.connect()
      return true
    } catch (error) {
      onNotice(error instanceof Error ? error.message : 'Local PRISM companion is unavailable.')
      return false
    }
  }

  async function createTemplate(template: Omit<SnippetTemplate, 'id' | 'custom'>) {
    if (!await ensureConnected()) throw new Error('Connect the local PRISM companion to save templates.')
    await api.request('templates', { method: 'POST', body: JSON.stringify(template) })
    await api.refreshTemplates()
    onNotice('Template saved to the local companion.')
  }

  async function deleteTemplate(id: string) {
    if (!api.ready || !window.confirm('Delete this local template?')) return
    try {
      await api.request(`templates/${encodeURIComponent(id)}`, { method: 'DELETE' })
      await api.refreshTemplates()
      onNotice('Template deleted.')
    } catch {
      onNotice('Could not delete this template.')
    }
  }

  async function clearHistory() {
    if (!api.ready || !window.confirm('Delete all local PRISM reports?')) return
    try {
      await api.request('reports', {
        method: 'DELETE',
        body: JSON.stringify({ confirm: true }),
      })
      await api.refreshHistory()
      onNotice('Local review history cleared.')
    } catch {
      onNotice('Could not clear local report history.')
    }
  }

  function exportHistory() {
    downloadJson('prism-reports.json', api.history)
  }

  function exportReport(report: ReviewReport | null) {
    if (report) downloadJson(`prism-${report.id ?? 'review'}.json`, report)
  }

  return {
    history: api.history,
    customTemplates: api.templates,
    createTemplate,
    deleteTemplate,
    clearHistory,
    exportHistory,
    exportReport,
  }
}
