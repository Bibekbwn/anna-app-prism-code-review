'use client'

import { useState } from 'react'
import type { LocalSettings } from './data'
import type { LocalPrismApi } from './use-local-prism'

export function usePrismPreferences(api: LocalPrismApi, onNotice: (message: string) => void) {
  const [effortOverride, setEffortOverride] = useState<string | null>(null)
  const [themeOverride, setThemeOverride] = useState<string | null>(null)
  const [suggestionsOverride, setSuggestionsOverride] = useState<boolean | null>(null)
  const effort = effortOverride ?? api.settings?.effort ?? 'Balanced'
  const theme = themeOverride ?? api.settings?.theme ?? 'Dark'
  const suggestions = suggestionsOverride ?? api.settings?.showSuggestions ?? true

  function clearOverrides() {
    setEffortOverride(null)
    setThemeOverride(null)
    setSuggestionsOverride(null)
  }

  function resetOverrides() {
    setEffortOverride('Balanced')
    setThemeOverride('Dark')
    setSuggestionsOverride(true)
  }

  async function save() {
    try {
      if (!api.ready) await api.connect()
      const settings = await api.request<LocalSettings>('settings', {
        method: 'PUT',
        body: JSON.stringify({ effort, theme, showSuggestions: suggestions }),
      })
      await api.refreshSettings(settings, { revalidate: false })
      clearOverrides()
      onNotice('Preferences saved to the local companion.')
    } catch (error) {
      onNotice(error instanceof Error ? error.message : 'Could not save local preferences.')
    }
  }

  async function reset() {
    resetOverrides()
    if (!api.ready) {
      onNotice('Preferences reset for this session.')
      return
    }
    try {
      const settings = await api.request<LocalSettings>('settings', {
        method: 'PUT',
        body: JSON.stringify({ effort: 'Balanced', theme: 'Dark', showSuggestions: true }),
      })
      await api.refreshSettings(settings, { revalidate: false })
      clearOverrides()
      onNotice('Local preferences reset.')
    } catch {
      onNotice('Preferences reset for this session; local companion could not be updated.')
    }
  }

  return {
    effort,
    setEffort: setEffortOverride,
    theme,
    setTheme: setThemeOverride,
    suggestions,
    setSuggestions: setSuggestionsOverride,
    save,
    reset,
  }
}
