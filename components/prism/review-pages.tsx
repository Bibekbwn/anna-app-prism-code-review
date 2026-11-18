import {
  ArrowRight,
  Bot,
  Code2,
  Download,
  FileCode2,
  History,
  ShieldCheck,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ReviewCategoryScores, ReviewHistoryEntry, ReviewReport } from './data'
import { languages } from './data'

const scoreCategories: { key: keyof ReviewCategoryScores; label: string }[] = [
  { key: 'quality', label: 'Code quality' },
  { key: 'security', label: 'Security' },
  { key: 'efficiency', label: 'Efficiency' },
  { key: 'testing', label: 'Testing' },
  { key: 'accessibility', label: 'Accessibility' },
]

type NewReviewPageProps = {
  code: string
  setCode: (value: string) => void
  language: string
  setLanguage: (value: string) => void
  effort: string
  setEffort: (value: string) => void
  connectionStatus: 'not-checked' | 'connecting' | 'ready' | 'error'
  aiConfigured: boolean
  aiProvider: string
  isReviewing: boolean
  onConnect: () => void
  onLoadSample: () => void
  onReview: () => void
}

export function NewReviewPage(props: NewReviewPageProps) {
  const statusText = {
    'not-checked': 'Start the local companion to use the PRISM review engine.',
    connecting: 'Connecting to the local PRISM engine…',
    ready: props.aiConfigured
      ? `Regex and AI review ready · ${props.aiProvider}`
      : 'Regex review ready · configure a provider key to enable AI findings.',
    error: 'The local companion could not be reached. Check that it is running.',
  }[props.connectionStatus]

  return (
    <section className="center-stage">
      <ReviewHero />
      <ReviewEditor {...props} />
      <EngineFeatures status={props.connectionStatus} statusText={statusText} onConnect={props.onConnect} />
    </section>
  )
}

function ReviewHero() {
  return (
    <div className="hero">
      <div className="hero-icon" aria-hidden="true"><PrismMark /></div>
      <h1>Ready to review</h1>
      <p>Paste code below or load a sample to explore the PRISM engine.</p>
    </div>
  )
}

function ReviewEditor({
  code,
  setCode,
  language,
  setLanguage,
  effort,
  setEffort,
  isReviewing,
  onLoadSample,
  onReview,
}: NewReviewPageProps) {
  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    const isComposing = event.nativeEvent.isComposing || event.keyCode === 229
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && !isComposing) {
      event.preventDefault()
      onReview()
    }
  }

  return (
    <section className="editor-card">
      <div className="editor-head">
        <span className="traffic traffic-red" />
        <span className="traffic traffic-yellow" />
        <span className="traffic traffic-green" />
        <span className="editor-file">PRISM</span>
        <span className="editor-shortcut">Ctrl + Enter to review</span>
        <Button variant="outline" size="sm" onClick={onLoadSample}>Load sample</Button>
      </div>
      <label className="sr-only" htmlFor="review-code">Code to review</label>
      <textarea
        id="review-code"
        className="code-editor"
        value={code}
        onChange={(event) => setCode(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type #prism-review here"
        spellCheck={false}
      />
      <div className="editor-controls">
        <label className="field">
          <span>Language</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="Auto-detect">Auto-detect</option>
            {languages.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label className="field">
          <span>Effort</span>
          <select value={effort} onChange={(event) => setEffort(event.target.value)}>
            <option>Lite</option>
            <option>Balanced</option>
            <option>Max</option>
          </select>
        </label>
        <Button className="review-button" disabled={isReviewing} onClick={onReview}>
          <Sparkles data-icon="inline-start" />
          {isReviewing ? 'Reviewing…' : 'Review'}
        </Button>
      </div>
      <p className="editor-hint">
        <ShieldCheck aria-hidden="true" /> Regex checks run locally. AI providers receive code only when configured; no tests are run.
      </p>
    </section>
  )
}

function EngineFeatures({
  status,
  statusText,
  onConnect,
}: {
  status: NewReviewPageProps['connectionStatus']
  statusText: string
  onConnect: () => void
}) {
  return (
    <div className="feature-row">
      <article className="feature-card">
        <Code2 aria-hidden="true" />
        <div>
          <strong>12 languages supported</strong>
          <span>Four deterministic regex agents plus six AI agents.</span>
        </div>
      </article>
      <article className="feature-card local-engine-card">
        <Bot aria-hidden="true" />
        <div>
          <strong>{status === 'ready' ? 'Local PRISM engine connected' : 'Local PRISM engine'}</strong>
          <span role="status" aria-live="polite">{statusText}</span>
        </div>
        {status !== 'ready' && <Button variant="outline" size="sm" onClick={onConnect}>Connect</Button>}
      </article>
    </div>
  )
}

export function ReviewResultsPage({
  report,
  language,
  effort,
  showSuggestions,
  onNewReview,
  onExport,
}: {
  report: ReviewReport | null
  language: string
  effort: string
  showSuggestions: boolean
  onNewReview: () => void
  onExport: () => void
}) {
  if (!report) {
    return (
      <>
        <PageHeading title="Review Results" description="Your PRISM findings appear here after a review." />
        <EmptyPanel
          icon={<FileCode2 aria-hidden="true" />}
          title="No review results yet"
          description="Connect the local companion, then submit code to run PRISM’s regex and AI agents."
          action="Start a review"
          onAction={onNewReview}
        />
      </>
    )
  }

  const blocking = report.blocking ?? report.findings.filter((finding) => finding.blocking).length

  return (
    <>
      <ResultsHeading report={report} language={language} effort={effort} onExport={onExport} />
      <ResultStats report={report} blocking={blocking} />
      <CategoryBreakdown scores={report.categoryScores} />
      <ReviewSummary report={report} />
      <FindingsSection report={report} blocking={blocking} showSuggestions={showSuggestions} onNewReview={onNewReview} />
      <p className="tests-note">Static analysis only; no tests were run.</p>
    </>
  )
}

function ResultsHeading({
  report,
  language,
  effort,
  onExport,
}: {
  report: ReviewReport
  language: string
  effort: string
  onExport: () => void
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>Review Results</h1>
        <p>{report.fileName ?? 'Pasted snippet'} · {language} · {effort} effort · {report.findings.length} findings</p>
      </div>
      <Button variant="outline" size="sm" onClick={onExport}>
        <Download data-icon="inline-start" /> Export report
      </Button>
    </div>
  )
}

function ResultStats({ report, blocking }: { report: ReviewReport; blocking: number }) {
  const risk = Math.round((report.riskScore ?? 0) * 100)
  const aiCalls = report.tokenUsage?.calls ?? 0
  return (
    <div className="result-stats">
      <StatCard label="Findings" value={String(report.findings.length)} accent="cyan" />
      <StatCard label="Blocking" value={String(blocking)} accent="red" />
      <StatCard label="Risk score" value={`${risk}%`} accent="amber" />
      <StatCard label="AI calls" value={String(aiCalls)} accent="violet" />
    </div>
  )
}

function CategoryBreakdown({ scores }: { scores?: ReviewCategoryScores }) {
  return (
    <section className="quality-score-section" aria-labelledby="quality-score-title">
      <div className="quality-score-header">
        <h2 id="quality-score-title">Quality breakdown</h2>
        <p>Severity-weighted findings determine scores; unrun checks show Not assessed.</p>
      </div>
      {scores ? (
        <div className="category-score-grid">
          {scoreCategories.map(({ key, label }) => (
            <CategoryScoreCard key={key} label={label} result={scores[key]} />
          ))}
        </div>
      ) : (
        <p className="score-not-available">This saved report predates category scoring.</p>
      )}
    </section>
  )
}

function ReviewSummary({ report }: { report: ReviewReport }) {
  return (
    <section className="report-summary">
      <div className="summary-heading"><Sparkles aria-hidden="true" /><strong>Review summary</strong></div>
      <p>{report.summary}</p>
      <span className={report.commitAllowed === false ? 'verdict blocked' : 'verdict passed'}>
        {report.commitAllowed === false ? 'Review gate blocked' : 'No blocking findings'}
      </span>
    </section>
  )
}

function FindingsSection({
  report,
  blocking,
  showSuggestions,
  onNewReview,
}: {
  report: ReviewReport
  blocking: number
  showSuggestions: boolean
  onNewReview: () => void
}) {
  return (
    <>
      <div className="results-toolbar">
        <span>Findings</span>
        <span>{report.findings.length} total · {blocking} blocking</span>
        <Button variant="outline" size="sm" onClick={onNewReview}>New review</Button>
      </div>
      {report.findings.length === 0 ? (
        <div className="result-clear">No actionable findings were identified. PRISM analyzes code but does not run tests.</div>
      ) : (
        <div className="finding-list">
          {report.findings.map((finding) => (
            <FindingCard key={`${finding.id}-${finding.file ?? ''}-${finding.line ?? 0}`} finding={finding} showSuggestions={showSuggestions} />
          ))}
        </div>
      )}
    </>
  )
}

function FindingCard({ finding, showSuggestions }: { finding: ReviewReport['findings'][number]; showSuggestions: boolean }) {
  return (
    <article className="finding-card">
      <div className="finding-meta">
        <span className={`severity-badge severity-${finding.severity.toLowerCase()}`}>{finding.severity}</span>
        <span className="finding-id">{finding.ruleId ?? finding.id}</span>
        {finding.agent && <span className="finding-agent">{finding.agent}</span>}
        {finding.file && <span className="finding-location">{finding.file}{finding.line ? `:${finding.line}` : ''}</span>}
        {typeof finding.confidence === 'number' && <span className="finding-confidence">{Math.round(finding.confidence * 100)}%</span>}
      </div>
      <h2>{finding.title}</h2>
      <p>{finding.message}</p>
      {finding.corroboratedBy?.length ? <div className="corroboration">Also reported by {finding.corroboratedBy.join(', ')}</div> : null}
      {finding.recommendation && <div className="recommendation"><ShieldCheck aria-hidden="true" /><span>{finding.recommendation}</span></div>}
      {showSuggestions && finding.suggestedFix && (
        <div className="suggested-fix">
          <strong>Suggested fix</strong>
          <pre>{finding.suggestedFix}</pre>
        </div>
      )}
    </article>
  )
}

export function ReviewHistoryPage({
  entries,
  onOpen,
  onNewReview,
  onExport,
  onClear,
}: {
  entries: ReviewHistoryEntry[]
  onOpen: (entry: ReviewHistoryEntry) => void
  onNewReview: () => void
  onExport: () => void
  onClear: () => void
}) {
  return (
    <>
      <div className="page-heading page-heading-tools">
        <div>
          <h1>Review History</h1>
          <p>{entries.length ? `${entries.length} local review${entries.length === 1 ? '' : 's'}.` : 'Completed local reviews will be listed here.'}</p>
        </div>
        {entries.length > 0 && <div className="toolbar-actions">
          <Button variant="outline" size="sm" onClick={onExport}><Download data-icon="inline-start" /> Export</Button>
          <Button variant="outline" size="sm" onClick={onClear}><Trash2 data-icon="inline-start" /> Clear history</Button>
        </div>}
      </div>
      {entries.length === 0 ? (
        <EmptyPanel
          icon={<History aria-hidden="true" />}
          title="No reviews yet"
          description="Run a review to start building your local PRISM history."
          action="Start a review"
          onAction={onNewReview}
        />
      ) : (
        <div className="history-table-wrap">
          <table className="history-table">
            <thead><tr><th>Date &amp; time</th><th>Language</th><th>Effort</th><th>Findings</th><th>Snippet</th><th>Open</th></tr></thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.date).toLocaleString()}</td>
                  <td><span className="language-tag">{entry.language}</span></td>
                  <td>{entry.effort}</td>
                  <td>{entry.report.findings.length}</td>
                  <td>{entry.fileName}</td>
                  <td><button className="history-open" aria-label={`Open review from ${entry.date}`} onClick={() => onOpen(entry)}><ArrowRight aria-hidden="true" /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

export function PageHeading({ title, description }: { title: string; description: string }) {
  return <div className="page-heading"><div><h1>{title}</h1><p>{description}</p></div></div>
}

function CategoryScoreCard({
  label,
  result,
}: {
  label: string
  result: ReviewCategoryScores[keyof ReviewCategoryScores]
}) {
  const value = result.score
  return (
    <article className="category-score-card">
      <div className="category-score-header">
        <h3>{label}</h3>
        <strong>{value === null ? 'Not assessed' : `${value}/100`}</strong>
      </div>
      {value !== null && (
        <div
          className={`category-score-track ${value >= 90 ? 'score-high' : value >= 70 ? 'score-mid' : 'score-low'}`}
          role="progressbar"
          aria-label={`${label} score`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={value}
          aria-valuetext={`${value} out of 100`}
        >
          <span style={{ width: `${value}%` }} />
        </div>
      )}
      <p>{result.method}</p>
      <small>{result.findings} related finding{result.findings === 1 ? '' : 's'}</small>
    </article>
  )
}

function StatCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  return <section className="stat-card"><div className={`stat-dot ${accent}`} /><span>{label}</span><strong className={accent}>{value}</strong></section>
}

function EmptyPanel({
  icon,
  title,
  description,
  action,
  onAction,
}: {
  icon: React.ReactNode
  title: string
  description: string
  action: string
  onAction: () => void
}) {
  return (
    <section className="empty-panel">
      <div className="empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{description}</p>
      <Button onClick={onAction}>{action}<ArrowRight data-icon="inline-end" /></Button>
    </section>
  )
}

function PrismMark() {
  return (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M16 3 28 25H4L16 3Z" />
      <path d="M16 3v13m0 0L4 25m12-9 12 9" />
    </svg>
  )
}
