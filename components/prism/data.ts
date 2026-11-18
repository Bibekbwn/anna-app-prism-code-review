export type PageId = 'new' | 'results' | 'history' | 'templates' | 'compare' | 'preferences'
export type FindingSeverity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Info'

export type ReviewFinding = {
  id: string
  severity: FindingSeverity
  title: string
  message: string
  recommendation: string
  file?: string
  line?: number
  suggestedFix?: string
  agent?: string
  confidence?: number
  ruleId?: string | null
  corroboratedBy?: string[]
  blocking?: boolean
}

export type TokenUsage = {
  calls?: number
  input_tokens?: number
  output_tokens?: number
  total_tokens?: number
  estimated_calls?: number
}

export type ReviewCategory = 'security' | 'quality' | 'efficiency' | 'testing' | 'accessibility'

export type CategoryScore = {
  score: number | null
  assessed: boolean
  findings: number
  method: string
}

export type ReviewCategoryScores = Record<ReviewCategory, CategoryScore>

export type ReviewReport = {
  id?: string
  date?: string
  effort?: string
  fileName?: string
  summary: string
  language: string
  findings: ReviewFinding[]
  riskScore?: number
  blocking?: number
  commitAllowed?: boolean
  qualityGatesPassed?: boolean
  tokenUsage?: TokenUsage
  categoryScores?: ReviewCategoryScores
  testsRun: false
}

export type ReviewHistoryEntry = {
  id: string
  date: string
  language: string
  effort: string
  fileName: string
  report: ReviewReport
}

export type SnippetTemplate = {
  id?: string
  name: string
  description: string
  code: string
  custom?: boolean
}

export type LocalSettings = {
  effort: string
  theme: string
  showSuggestions: boolean
}

export type BackendStatus = {
  ok: boolean
  version: string
  engine: string
  regexAvailable: boolean
  ai: {
    configured: boolean
    keyConfigured?: boolean
    sdkInstalled?: boolean
    provider: string
    reason?: string | null
  }
}

export const pages: { id: PageId; label: string }[] = [
  { id: 'new', label: 'New Review' },
  { id: 'results', label: 'Review Results' },
  { id: 'history', label: 'Review History' },
  { id: 'templates', label: 'Snippet Templates' },
  { id: 'compare', label: 'Code Compare' },
  { id: 'preferences', label: 'Preferences' },
]

export const languages = [
  'Python',
  'JavaScript / TypeScript',
  'Go',
  'Rust',
  'Java',
  'C#',
  'C',
  'C++',
  'Ruby',
  'PHP',
  'Kotlin',
  'Swift',
]

export const sampleCode = `from pathlib import Path

def summarize_files(paths):
    return [Path(path).name for path in paths]

print(summarize_files(["report.csv", "notes.txt"]))`

export const snippetTemplates: SnippetTemplate[] = [
  {
    name: 'Environment secrets',
    description: 'Read credentials from the environment',
    code: 'STRIPE_KEY = os.environ["STRIPE_SECRET_KEY"]\nAWS_SECRET = os.environ["AWS_SECRET"]',
  },
  {
    name: 'Safe JSON parsing',
    description: 'Parse structured input',
    code: 'value = json.loads(user_input)\nvalidate_payload(value)',
  },
  {
    name: 'Parameterized query',
    description: 'Bind user input as a value',
    code: 'cursor.execute("SELECT * FROM users WHERE name = ?", (username,))',
  },
  {
    name: 'Used imports',
    description: 'Keep imports purposeful',
    code: 'import json\nconfig = json.loads("{}")',
  },
  {
    name: 'Small helpers',
    description: 'Keep functions focused',
    code: 'def validate_checkout(request):\n    return request.is_valid\n\ndef process_checkout(request):\n    validate_checkout(request)\n    return charge(request)',
  },
]
