'use client'

import { useEffect, useState } from 'react'

export type AnnaRuntime = {
  window: {
    set_title: (input: { title: string }) => Promise<unknown>
  }
}

type AnnaRuntimeEvent = CustomEvent<AnnaRuntime>

export function useAnnaRuntime(title: string) {
  const [runtime, setRuntime] = useState<AnnaRuntime | null>(null)

  useEffect(() => {
    const query = new URLSearchParams(window.location.search)
    if (!query.has('wid') || !query.has('t')) return

    const onReady = (event: Event) => setRuntime((event as AnnaRuntimeEvent).detail)
    const onError = () => undefined
    const script = document.createElement('script')
    script.type = 'module'
    script.src = new URL('anna-runtime-loader.js', document.baseURI).toString()
    script.onerror = onError
    window.addEventListener('anna-runtime-ready', onReady)
    window.addEventListener('anna-runtime-error', onError)
    document.head.append(script)

    return () => {
      window.removeEventListener('anna-runtime-ready', onReady)
      window.removeEventListener('anna-runtime-error', onError)
      script.remove()
    }
  }, [])

  useEffect(() => {
    if (!runtime) return
    void runtime.window.set_title({ title: `PRISM · ${title}` }).catch(() => undefined)
  }, [runtime, title])
}
