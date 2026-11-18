export const DEFAULT_PRISM_API_URL =
  process.env.NEXT_PUBLIC_PRISM_LOCAL_URL?.trim() || 'http://localhost:8765'

export function normalizePrismApiUrl(value: string) {
  try {
    const url = new URL(value.trim())
    if (!['http:', 'https:'].includes(url.protocol)) return null
    if (!['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) return null
    return url.origin
  } catch {
    return null
  }
}

export async function prismApiRequest<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  headers.set('X-PRISM-Client', 'web')
  if (init.body) headers.set('Content-Type', 'application/json')

  const response = await fetch(url, { ...init, headers, cache: 'no-store' })
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const message = typeof payload?.error === 'string' ? payload.error : `PRISM companion returned ${response.status}.`
    throw new Error(message)
  }
  return payload as T
}
