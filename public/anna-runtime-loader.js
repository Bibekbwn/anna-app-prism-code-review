try {
  const { AnnaAppRuntime } = await import('/static/anna-apps/_sdk/latest/index.js')
  const runtime = await AnnaAppRuntime.connect()
  window.dispatchEvent(new CustomEvent('anna-runtime-ready', { detail: runtime }))
} catch {
  window.dispatchEvent(new CustomEvent('anna-runtime-error'))
}
