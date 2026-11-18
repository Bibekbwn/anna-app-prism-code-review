'use client'

import { useState } from 'react'
import useSWR from 'swr'
import type { BackendStatus, LocalSettings, ReviewHistoryEntry, SnippetTemplate } from './data'
import { DEFAULT_PRISM_API_URL, normalizePrismApiUrl, prismApiRequest } from './local-api'

export type ConnectionStatus = 'not-checked' | 'connecting' | 'ready' | 'error'

export function useLocalPrismApi() {
  const [localUrl, setLocalUrlState] = useState(DEFAULT_PRISM_API_URL)
  const [connectionRequested, setConnectionRequested] = useState(false)
  const [connectionAttempt, setConnectionAttempt] = useState<'idle' | 'connecting' | 'error'>('idle')
  const [statusOverride, setStatusOverride] = useState<BackendStatus | null>(null)
  const apiOrigin = normalizePrismApiUrl(localUrl)
  const statusKey = connectionRequested && apiOrigin ? `${apiOrigin}/api/health` : null
  const { data: statusData, error: statusError } = useSWR<BackendStatus>(
    statusKey,
    (url: string) => prismApiRequest<BackendStatus>(url),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )
  const status = statusData ?? statusOverride
  const ready = status?.ok === true
  const connectionStatus: ConnectionStatus = ready
    ? 'ready'
    : connectionAttempt === 'connecting'
      ? 'connecting'
      : connectionAttempt === 'error' || Boolean(statusError)
        ? 'error'
        : 'not-checked'
  const settingsKey = ready && apiOrigin ? `${apiOrigin}/api/settings` : null
  const historyKey = ready && apiOrigin ? `${apiOrigin}/api/reports` : null
  const templatesKey = ready && apiOrigin ? `${apiOrigin}/api/templates` : null
  const { data: settings, mutate: refreshSettings } = useSWR<LocalSettings>(
    settingsKey,
    (url: string) => prismApiRequest<LocalSettings>(url),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )
  const { data: history = [], mutate: refreshHistory } = useSWR<ReviewHistoryEntry[]>(
    historyKey,
    (url: string) => prismApiRequest<ReviewHistoryEntry[]>(url),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )
  const { data: templates = [], mutate: refreshTemplates } = useSWR<SnippetTemplate[]>(
    templatesKey,
    (url: string) => prismApiRequest<SnippetTemplate[]>(url),
    { shouldRetryOnError: false, revalidateOnFocus: false },
  )

  function setLocalUrl(value: string) {
    setLocalUrlState(value)
    setConnectionRequested(false)
    setStatusOverride(null)
    setConnectionAttempt('idle')
  }

  async function connect() {
    if (!apiOrigin) {
      setConnectionAttempt('error')
      throw new Error('Use a loopback address such as http://localhost:8765.')
    }

    setConnectionAttempt('connecting')
    try {
      const response = await prismApiRequest<BackendStatus>(`${apiOrigin}/api/health`)
      if (!response.ok || !response.regexAvailable) throw new Error('PRISM engine unavailable')
      setStatusOverride(response)
      setConnectionRequested(true)
      setConnectionAttempt('idle')
      return response
    } catch {
      setConnectionRequested(false)
      setConnectionAttempt('error')
      throw new Error('Could not reach the local PRISM companion. Start it on your machine and try again.')
    }
  }

  async function request<T>(path: string, init: RequestInit = {}) {
    if (!apiOrigin) throw new Error('Use a loopback address such as http://localhost:8765.')
    return prismApiRequest<T>(`${apiOrigin}/api/${path.replace(/^\/+/, '')}`, init)
  }

  return {
    apiOrigin,
    localUrl,
    setLocalUrl,
    status,
    ready,
    connectionStatus,
    settings,
    history,
    templates,
    connect,
    request,
    refreshHistory,
    refreshSettings,
    refreshTemplates,
  }
}

export type LocalPrismApi = ReturnType<typeof useLocalPrismApi>
