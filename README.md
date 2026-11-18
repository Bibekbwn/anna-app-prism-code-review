# Anna AI OS - Code Review Prism

A full-stack AI application for the Anna AI OS Founding Builder Challenge 2026.

## 🌟 Features

- **Multi-Language Support**: 12 programming languages including Python, JavaScript/TypeScript, Go, Rust, Java, C#, C, C++, Ruby, PHP, Kotlin, and Swift
- **AI-Powered Code Review**: Accessibility, quality, and efficiency analysis
- **User Onboarding**: 4-step guided tour for new users
- **Environment Variable Configuration**: All defaults configurable
- **BYOK Support**: Bring Your Own Key (optional)
- **Responsive Design**: Works on mobile and desktop

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ or pnpm v12.3.4
- Python 3.11+
- Git

### Installation
```bash
git clone https://github.com/Bibekbwn/anna-app-prism-code-review.git
cd anna-app-prism-code-review
pnpm install
cd local-companion
pip install -r requirements.txt
```

### Environment Configuration
```env
PRISM_WEB_PORT=8765
PRISM_WEB_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
PRISM_VALID_EFFORTS="Lite,Balanced,Max"
PRISM_VALID_THEMES="Dark,Light"
PRISM_BYOK_ENABLED="false"
```

### Running the Application
```bash
# Terminal 1: Python companion
cd local-companion
python server.py

# Terminal 2: Next.js frontend
pnpm dev
```

Access at http://localhost:3000
```

## 📁 Project Structure

```
anna-app-prism-code-review/
├── package.json              # Node.js project configuration
├── tsconfig.json            # TypeScript configuration
├── tailwind.config.mjs      # Tailwind CSS config
├── postcss.config.mjs       # PostCSS configuration
├── vercel.json              # Vercel deployment config
├── .gitignore               # Git ignore rules
│
├── app/                     # Next.js 16 App Router
│   ├── page.tsx             # Main page with onboarding flow
│   ├── globals.css          # Custom styles
│   └── layout.tsx           # App layout
│
├── components/              # React components
│   ├── ui/                  # shadcn/ui components (button.tsx)
│   ├── onboarding/          # 4-step onboarding tour
│   │   └── onboarding.tsx
│   └── prism/               # PrismApp component
│
├── local-companion/         # Python PRISM web adapter
│   ├── server.py            # Main web server with improvements
│   ├── quality_metrics.py   # Accessibility & quality scoring
│   │   ├── LANGUAGE_ACCESSIBILITY_LEVEL (multi-language support)
│   │   └── accessibility_findings() (all-languages support)
│   ├── web_security.py      # Origin validation & loopback detection
│   ├── test_server.py       # Unit tests (7/7 passing)
│   ├── test_web_security.py # Web security tests
│   └── test_quality_metrics.py # Quality metrics tests
│
├── components.json          # shadcn component registry
├── next-env.d.ts           # Next.js TypeScript environments
└── README.md               # This file
```

## 🛠️ Development

### Running Tests
```bash
# Run all companion tests
python -m unittest discover -s local-companion -p 'test_*.py'

# Specific test files
python -m unittest discover -s local-companion -p 'test_server.py'
python -m unittest discover -s local-companion -p 'test_web_security.py'
python -m unittest discover -s local-companion -p 'test_quality_metrics.py'
```

### All 7 Original Tests Pass:
- ✅ Language detection (Python, JS/TS, Go)
- ✅ Input validation (empty code, unsupported languages, size limits)
- ✅ Settings round-trip and template filtering
- ✅ AI status key protection (no key leakage)
- ✅ Review input limits and invalid languages

### Challenge Integration
Ready for Anna AI OS Founding Builder Challenge 2026 with:
- Founding Builder Deadline: November 30, 2026
- Minimum 200 Qualified App MAU required
- Monthly grant tiers from 200 MAU ($50) to 20,000 MAU ($5,000)

## 📜 License

This project is licensed under the **MIT License** - see the LICENSE file included in the repository.

## 🙏 Acknowledgments

- **Anna AI OS** - For the Founding Builder Challenge 2026
- **PRISM CLI** - For the code review engine
- **shadcn/ui** - For the beautiful UI components
- **Tailwind CSS** - For the styling framework
- **All contributors** - For tests, improvements, and feedback

## 📞 Contact & Support

- **Anna Partners**: https://anna.partners
- **Builder Discord**: https://discord.gg/7ftTdsdMMz
- **Developer Docs**: https://anna.partners/developers
- **AI-readable Docs**: https://anna.partners/llms.txt

---

**Built with ❤️ for the Anna AI OS Founding Builder Challenge 2026**

*Ready for publication and MAU growth toward 200+ Qualified App MAU by November 30, 2026*