# PRISM Code Review — Anna App

Multi-agent code review app for the Anna AI OS. Combines 4 deterministic regex agents with 6 AI agents to detect security flaws, quality issues, policy violations, and test gaps. Produces a 0–100 score with grade (A–F), per-finding line numbers, and suggested fixes.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript 5.7, Tailwind CSS 4 |
| **UI Components** | shadcn/ui (`@base-ui/react`), lucide-react icons |
| **State Management** | SWR (data fetching), React hooks (local state) |
| **Local Backend** | Python 3.10+ HTTP server (`local-companion/server.py`) |
| **Review Engine** | `prism-code-review[all]==2.0.1` (CLI + AI agents) |
| **AI Providers** | Google Gemini, Anthropic Claude, OpenAI (configurable via env vars) |
| **Anna Integration** | Static SPA bundle (`anna-app/manifest.json`), served by Anna runtime |
| **Package Manager** | pnpm 12.3.4 |
| **Testing** | Python `unittest` (companion), TypeScript `tsc --noEmit` |

---

## Folder Structure

```
anna-app/
├── app/                          # Next.js app router
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Main entry page
│   └── globals.css               # Global styles
├── components/
│   └── prism/                    # PRISM React components
│       ├── prism-app.tsx         # Main app component (state, navigation)
│       ├── prism-header.tsx      # Top navigation bar
│       ├── prism-page-content.tsx # Page router (switches views)
│       ├── review-pages.tsx      # New Review, Review Results, Review History
│       ├── tools-pages.tsx       # Snippet Templates, Code Compare, Preferences
│       ├── data.ts              # Types, page definitions, sample code
│       ├── anna-runtime.ts      # Anna runtime loader (sets window title)
│       ├── use-local-prism.ts   # Local companion API hook (fetch, SWR)
│       ├── use-prism-review.ts  # Review submission logic
│       ├── use-prism-collections.ts  # Templates CRUD
│       ├── use-prism-preferences.ts # Settings (effort, theme, suggestions)
│       └── local-api.ts         # API request helpers
├── anna-app/                    # Anna App package
│   ├── manifest.json            # Anna manifest (schema 4, static-spa)
│   └── package-bundle.mjs       # Copies Next.js build → bundle/
├── local-companion/             # Python local backend
│   ├── server.py               # HTTP server (port 8765)
│   ├── prism.json              # Agent config (10 agents, quality gates)
│   ├── requirements.txt        # Python dependencies
│   ├── quality_metrics.py      # Category scoring
│   ├── web_security.py         # Origin validation, loopback checks
│   ├── test_*.py               # Unit tests
│   └── .gitignore
├── public/                     # Static assets (icons, logos)
├── components.json             # shadcn config
├── package.json                # Node dependencies and scripts
├── pnpm-workspace.yaml         # pnpm workspace config
├── next.config.mjs             # Next.js config (static export)
├── tsconfig.json               # TypeScript config
├── postcss.config.mjs          # PostCSS config
├── vercel.json                 # Vercel deploy config
└── .prismignore                # Files to ignore during bundle
```

---

## Installation

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | 20+ | Frontend build |
| pnpm | 12.x | Package manager |
| Python | 3.10+ | Local companion server |
| pip | latest | Python packages |

### 1. Clone and install frontend

```bash
cd anna-app
pnpm install
```

### 2. Install local companion (Python)

```bash
cd local-companion
python -m pip install -r requirements.txt
```

This installs `prism-code-review[all]==2.0.1` which includes the review engine and AI agents.

### 3. Configure AI provider (optional)

Set environment variables for the AI provider you want to use:

**Gemini (default):**
```bash
# Windows
set MODEL_PROVIDER=gemini
set GEMINI_API_KEY=your-key-here

# macOS/Linux
export MODEL_PROVIDER=gemini
export GEMINI_API_KEY=your-key-here
```

**Claude:**
```bash
set MODEL_PROVIDER=claude
set ANTHROPIC_API_KEY=your-key-here
```

**OpenAI:**
```bash
set MODEL_PROVIDER=openai
set OPENAI_API_KEY=your-key-here
```

Also install the Python SDK for your provider:
```bash
pip install google-generativeai   # Gemini
pip install anthropic              # Claude
pip install openai                 # OpenAI
```

Without an API key configured, PRISM runs in **regex-only mode** (4 deterministic agents, no AI).

### 4. Build and bundle for Anna

```bash
pnpm run anna:bundle
```

This runs `next build` (static export to `out/`) and copies it to `anna-app/bundle/`.

### 5. Start the local companion server

```bash
cd local-companion
python server.py
```

Output:
```
PRISM local companion: http://localhost:8765/api/health
Project data and reports stay in C:\...\local-companion
```

---

## How to Use

### Development (web app)

```bash
cd anna-app
pnpm run dev
```

Opens at `http://localhost:3000`. The app will show "not-checked" status for the local companion. Click **Connect** in the Preferences page to link to `http://localhost:8765`.

### Running reviews

1. **Connect**: Go to Preferences → click "Check connection" (requires companion server running on port 8765)
2. **Paste code**: Go to "New Review" → paste code in the editor
3. **Select language**: Auto-detect or choose from 12 languages
4. **Choose effort**:
   - **Lite**: Regex agents only (fast, no AI)
   - **Balanced**: Regex + AI agents (if configured)
   - **Max**: Full analysis with all agents
5. **Click Review**: Results appear with:
   - Risk score (0–100%), blocking count, findings count, AI calls
   - Quality breakdown (security, quality, efficiency, testing, accessibility)
   - Individual findings with severity, agent, confidence, and suggested fixes
6. **Review History**: All reviews saved locally, viewable and exportable as JSON

### Snippet Templates

- Built-in templates (5 samples) are loaded from `data.ts`
- Create custom templates via "New template" button (stored in companion)
- Delete custom templates via the trash icon

### Code Compare

Paste two versions of code to see a side-by-side diff with added/removed lines.

### AI Provider Setup

```bash
# Set provider and key locally (never in the web UI)
prism key set --global --provider gemini --key YOUR_KEY
```

The UI shows AI status:
- **Connected with AI**: Provider configured and SDK installed → all 10 agents run
- **Regex only**: No key or SDK missing → 4 regex agents only

---

## Architecture

```
┌─────────────────┐     fetch     ┌──────────────────────┐
│  Next.js Frontend│ ──────────→ │  Python Companion     │
│  (port 3000)     │ ←────────── │  (port 8765)         │
│                  │   JSON      │                      │
│  React + SWR     │             │  PRISM engine        │
└─────────────────┘             │  - 4 regex agents    │
                                │  - 6 AI agents       │
                                │  - Quality metrics   │
                                │  - Report storage    │
                                └──────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────────┐
                                │  AI Provider API     │
                                │  (Gemini/Claude/GPT) │
                                └──────────────────────┘
```

### Review Flow

1. User pastes code → clicks Review
2. Frontend sends `POST /api/reviews` with `{ code, language, effort }`
3. Companion validates request (max 40K chars, valid language/effort)
4. Runs `review_file()` from PRISM CLI engine
5. If AI configured: runs 6 AI agents (based on effort level)
6. Computes risk score, category scores, token usage
7. Saves report to `REPORTS_DIR/` as JSON
8. Returns report + AI status to frontend
9. Frontend displays findings, score, and AI call count

### API Endpoints (Local Companion)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Companion status, AI provider info |
| GET | `/api/settings` | Load settings (effort, theme, suggestions, templates) |
| PUT | `/api/settings` | Save settings |
| GET | `/api/templates` | List custom templates |
| POST | `/api/templates` | Create a template |
| DELETE | `/api/templates/:id` | Delete a template |
| GET | `/api/reports` | List recent reports |
| GET | `/api/reports/:id` | Get a specific report |
| POST | `/api/reviews` | Run a code review |
| DELETE | `/api/reports` | Clear all reports |

All endpoints require `X-PRISM-Client: web` header and loopback origin.

---

## Testing

```bash
# Run all tests
pnpm run test

# Run only companion tests
pnpm run test:companion

# Type check
pnpm exec tsc --noEmit
```

Companion tests cover: `test_web_security.py`, `test_quality_metrics.py`, `test_server.py`.

---

## Anna App Deployment

### Bundle creation

```bash
pnpm run anna:bundle
```

This builds the Next.js app to `out/` and copies it to `anna-app/bundle/`.

### Manifest

Located at `anna-app/manifest.json`:
- **Schema**: 4
- **Format**: static-spa
- **Entry**: `index.html`
- **Views**: `main` (single view, 360×400 min, 1024×720 default)
- **Form factors**: desktop + mobile
- **CSP**: Allows `localhost:8765` and `127.0.0.1:8765` for companion connection

### Important notes for Anna

- The app requires the **local companion server** to be running on the user's machine
- AI provider keys are **never** entered in the web UI — they're set locally via CLI
- The companion only accepts **loopback requests** (localhost/127.0.0.1)
- Website origins must be in `ALLOWED_ORIGINS` (defaults: localhost:3000, anna.partners, v0.build)
- The manifest has a **duplicate `csp_overrides`** key — this should be cleaned up before publishing

---

## Security Notes

- Companion server binds to `127.0.0.1` only (no remote access)
- Origin validation on all requests
- `X-PRISM-Client: web` header required
- Content-Type must be `application/json`
- Max request body: 180KB
- Max code size: 40,000 characters
- API keys are **never** sent to the frontend — only provider status (configured/not) is exposed
- Binary content (`\x00`) is rejected

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PROVIDER` | `gemini` | AI provider: `gemini`, `claude`, `openai` |
| `GEMINI_API_KEY` | — | Gemini API key |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `PRISM_WEB_PORT` | `8765` | Companion server port |
| `PRISM_WEB_ORIGINS` | — | Comma-separated additional allowed origins |
| `NEXT_PUBLIC_PRISM_LOCAL_URL` | `http://localhost:8765` | Frontend companion URL |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "PRISM companion unavailable" | Start `python local-companion/server.py` on port 8765 |
| "AI not configured" | Set `MODEL_PROVIDER` + API key env vars, install provider SDK |
| "Origin not allowed" | Add your domain to `PRISM_WEB_ORIGINS` |
| "Module not found: prism" | `pip install prism-code-review[all]==2.0.1` |
| TypeScript errors | Run `pnpm exec tsc --noEmit` |
| Build fails | Check `pnpm install` completed, Node 20+ installed |