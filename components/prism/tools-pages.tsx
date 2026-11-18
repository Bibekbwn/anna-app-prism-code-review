import { useMemo, useState, type FormEvent } from 'react'
import {
  ArrowRight,
  ArrowRightLeft,
  Check,
  FileCode2,
  Gauge,
  Lightbulb,
  Moon,
  Plus,
  RotateCcw,
  Search,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { snippetTemplates, type BackendStatus, type SnippetTemplate } from './data'
import { PageHeading } from './review-pages'

type SnippetTemplatesPageProps = {
  customTemplates: SnippetTemplate[]
  onUseTemplate: (code: string) => void
  onCreateTemplate: (template: Omit<SnippetTemplate, 'id' | 'custom'>) => Promise<void>
  onDeleteTemplate: (id: string) => Promise<void>
  onToast: (message: string) => void
}

export function SnippetTemplatesPage({
  customTemplates,
  onUseTemplate,
  onCreateTemplate,
  onDeleteTemplate,
  onToast,
}: SnippetTemplatesPageProps) {
  const [query, setQuery] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [code, setCode] = useState('')
  const [saving, setSaving] = useState(false)
  const allTemplates = useMemo(
    () => [
      ...snippetTemplates.map((item, index) => ({ ...item, id: `builtin-${index}`, custom: false })),
      ...customTemplates,
    ],
    [customTemplates],
  )
  const filteredTemplates = useMemo(
    () => allTemplates.filter((item) => `${item.name} ${item.description}`.toLowerCase().includes(query.toLowerCase())),
    [allTemplates, query],
  )

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim() || !code.trim()) return
    setSaving(true)
    try {
      await onCreateTemplate({ name: name.trim(), description: description.trim() || 'Custom template', code })
      setName('')
      setDescription('')
      setCode('')
      setFormOpen(false)
    } catch (error) {
      onToast(error instanceof Error ? error.message : 'Could not save template.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div className="page-heading page-heading-tools">
        <div>
          <h1>Snippet Templates</h1>
          <p>Load a sample pattern into the editor or save your own local template.</p>
        </div>
        <div className="toolbar-actions">
          <label className="search-field">
            <Search aria-hidden="true" />
            <span className="sr-only">Search templates</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search templates" />
          </label>
          <Button variant="outline" size="sm" onClick={() => setFormOpen(true)}>
            <Plus data-icon="inline-start" /> New template
          </Button>
        </div>
      </div>
      {formOpen && (
        <form className="template-editor" onSubmit={handleSubmit}>
          <div className="template-form-fields">
            <label className="field"><span>Template name</span><input required maxLength={80} value={name} onChange={(event) => setName(event.target.value)} /></label>
            <label className="field"><span>Description</span><input maxLength={160} value={description} onChange={(event) => setDescription(event.target.value)} /></label>
          </div>
          <label className="field"><span>Code snippet</span><textarea required maxLength={10000} value={code} onChange={(event) => setCode(event.target.value)} /></label>
          <div className="template-form-actions">
            <Button type="button" variant="outline" size="sm" onClick={() => setFormOpen(false)}>Cancel</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Saving…' : 'Save template'}</Button>
          </div>
        </form>
      )}
      <div className="template-grid">
        {filteredTemplates.map((template, index) => (
          <article className="template-card" key={template.id ?? template.name}>
            <div className="template-heading">
              <span className="template-icon"><FileCode2 aria-hidden="true" /></span>
              <div>
                <h2>{template.name}</h2>
                <p>{template.description}</p>
              </div>
              {template.custom ? (
                <button className="template-delete" aria-label={`Delete ${template.name}`} onClick={() => template.id && onDeleteTemplate(template.id)}><Trash2 aria-hidden="true" /></button>
              ) : (
                <span className="template-number">{String(index + 1).padStart(2, '0')}</span>
              )}
            </div>
            <pre>{template.code}</pre>
            <button className="template-use" onClick={() => onUseTemplate(template.code)}>
              Use template <ArrowRight aria-hidden="true" />
            </button>
          </article>
        ))}
        {filteredTemplates.length === 0 && <div className="template-empty">No templates match that search.</div>}
        <button className="template-create" onClick={() => setFormOpen(true)}>
          <Plus aria-hidden="true" />
          <strong>Save your own snippet template</strong>
          <span>Custom templates are stored with your local PRISM companion.</span>
        </button>
      </div>
    </>
  )
}

type DiffRow = { kind: 'matching' | 'added' | 'removed'; lineNumber: number; content: string }

export function CodeComparePage({ onToast }: { onToast: (message: string) => void }) {
  const [original, setOriginal] = useState('')
  const [revised, setRevised] = useState('')
  const [diff, setDiff] = useState<DiffRow[] | null>(null)

  function updateOriginal(value: string) {
    setOriginal(value)
    setDiff(null)
  }

  function updateRevised(value: string) {
    setRevised(value)
    setDiff(null)
  }

  function compare() {
    if (!original.trim() || !revised.trim()) {
      onToast('Paste both versions before comparing')
      return
    }

    const oldLines = original.split('\n')
    const newLines = revised.split('\n')
    const rows: DiffRow[] = []

    for (let index = 0; index < Math.max(oldLines.length, newLines.length); index += 1) {
      const oldLine = oldLines[index]
      const newLine = newLines[index]
      if (oldLine === newLine) {
        rows.push({ kind: 'matching', lineNumber: index + 1, content: oldLine ?? '' })
      } else {
        if (oldLine !== undefined) rows.push({ kind: 'removed', lineNumber: index + 1, content: oldLine })
        if (newLine !== undefined) rows.push({ kind: 'added', lineNumber: index + 1, content: newLine })
      }
    }

    setDiff(rows)
  }

  function swapSides() {
    setOriginal(revised)
    setRevised(original)
    setDiff(null)
  }

  return (
    <>
      <div className="page-heading page-heading-tools">
        <div>
          <h1>Code Compare</h1>
          <p>Paste both versions to see exactly what changed.</p>
        </div>
        <Button variant="outline" size="sm" onClick={swapSides}>
          <ArrowRightLeft data-icon="inline-start" /> Swap sides
        </Button>
      </div>
      <div className="compare-grid">
        <section className="code-panel">
          <div className="code-panel-heading"><span>Original</span></div>
          <label className="sr-only" htmlFor="original-code">Original code</label>
          <textarea id="original-code" className="compare-editor" value={original} onChange={(event) => updateOriginal(event.target.value)} placeholder="Paste original code here" spellCheck={false} />
        </section>
        <section className="code-panel">
          <div className="code-panel-heading"><span>Revised</span></div>
          <label className="sr-only" htmlFor="revised-code">Revised code</label>
          <textarea id="revised-code" className="compare-editor" value={revised} onChange={(event) => updateRevised(event.target.value)} placeholder="Paste revised code here" spellCheck={false} />
        </section>
      </div>
      <div className="compare-actions">
        <Button onClick={compare}><ArrowRightLeft data-icon="inline-start" /> Compare</Button>
        {diff && <span className="diff-count">{diff.filter((row) => row.kind === 'added').length} added · {diff.filter((row) => row.kind === 'removed').length} removed</span>}
      </div>
      <section className="diff-panel">
        <div className="diff-heading"><h2>Diff output</h2></div>
        {diff === null ? (
          <div className="diff-empty">Compare two versions to see the differences here.</div>
        ) : diff.length ? (
          <div className="diff-rows">
            {diff.map((row, index) => (
              <div className={`diff-row ${row.kind}`} key={`${row.lineNumber}-${row.kind}-${index}`}>
                <span>{row.lineNumber}</span>
                <code>{row.kind === 'added' ? '+ ' : row.kind === 'removed' ? '− ' : '  '}{row.content}</code>
              </div>
            ))}
          </div>
        ) : <div className="diff-empty">No differences found.</div>}
      </section>
    </>
  )
}

type PreferencesPageProps = {
  effort: string
  setEffort: (value: string) => void
  theme: string
  setTheme: (value: string) => void
  suggestions: boolean
  setSuggestions: (value: boolean) => void
  localUrl: string
  setLocalUrl: (value: string) => void
  connectionStatus: 'not-checked' | 'connecting' | 'ready' | 'error'
  backendStatus: BackendStatus | null
  onConnect: () => void
  onSave: () => void
  onReset: () => void
}

export function PreferencesPage({
  effort,
  setEffort,
  theme,
  setTheme,
  suggestions,
  setSuggestions,
  localUrl,
  setLocalUrl,
  connectionStatus,
  backendStatus,
  onConnect,
  onSave,
  onReset,
}: PreferencesPageProps) {
  const statusLabel = connectionStatus === 'ready'
    ? `Connected · PRISM ${backendStatus?.version ?? ''}`
    : connectionStatus === 'connecting'
      ? 'Checking local companion…'
      : connectionStatus === 'error'
        ? 'Not reachable'
        : 'Not checked'

  return (
    <>
      <PageHeading title="Preferences" description="Set local defaults and connect the Python review engine." />
      <section className="local-engine-settings">
        <div className="local-engine-heading">
          <div>
            <span className={`connection-dot ${connectionStatus === 'ready' ? 'connected' : ''}`} />
            <strong>Local PRISM companion</strong>
            <span className="connection-state">{statusLabel}</span>
          </div>
          <Button variant="outline" size="sm" onClick={onConnect}>Check connection</Button>
        </div>
        <label className="field local-url-field">
          <span>Local API address</span>
          <input value={localUrl} onChange={(event) => setLocalUrl(event.target.value)} spellCheck={false} />
        </label>
        <div className="local-setup-note">
          <p>On your machine, install the companion requirements and run the local server:</p>
          <code>python -m pip install -r local-companion/requirements.txt</code>
          <code>python local-companion/server.py</code>
          <p>Regex runs locally. AI review sends code to your configured provider; PRISM never executes it or runs tests.</p>
          <p>Set an AI key locally with <code>prism key set --global --provider gemini --key YOUR_KEY</code>. Never enter provider keys in this website.</p>
          <p>For another website domain, add its exact origin to <code>PRISM_WEB_ORIGINS</code> before starting the companion. Browsers may request local-network access.</p>
        </div>
      </section>
      <div className="preferences-grid">
        <section className="preference-card">
          <div className="preference-icon"><Gauge aria-hidden="true" /></div>
          <h2>Default effort</h2>
          <p>Lite runs regex only; Balanced and Max include configured AI agents.</p>
          <label className="sr-only" htmlFor="default-effort">Default effort</label>
          <select id="default-effort" value={effort} onChange={(event) => setEffort(event.target.value)}>
            <option>Lite</option>
            <option>Balanced</option>
            <option>Max</option>
          </select>
        </section>
        <section className="preference-card">
          <div className="preference-icon"><Moon aria-hidden="true" /></div>
          <h2>Theme</h2>
          <p>Set the appearance for this workspace.</p>
          <label className="sr-only" htmlFor="workspace-theme">Theme</label>
          <select id="workspace-theme" value={theme} onChange={(event) => setTheme(event.target.value)}>
            <option>Dark</option>
            <option>Light</option>
          </select>
        </section>
        <section className="preference-card">
          <div className="preference-icon"><Lightbulb aria-hidden="true" /></div>
          <h2>Show AI suggestions</h2>
          <p>Display suggested fixes alongside review findings.</p>
          <label className="toggle-row">
            <input type="checkbox" checked={suggestions} onChange={(event) => setSuggestions(event.target.checked)} />
            <span>Enabled</span>
          </label>
        </section>
      </div>
      <div className="preferences-footer">
        <span>Preferences and reports stay in the local companion folder.</span>
        <div>
          <Button variant="outline" size="sm" onClick={onReset}><RotateCcw data-icon="inline-start" /> Reset</Button>
          <Button size="sm" onClick={onSave}><Check data-icon="inline-start" /> Save preferences</Button>
        </div>
      </div>
    </>
  )
}
