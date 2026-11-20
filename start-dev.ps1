# Start both Anna AI OS services with one command
Write-Host "🚀 Starting Anna AI OS Code Review Prism..." -ForegroundColor Cyan

# Check if Python companion requirements are installed
Write-Host "📦 Checking Python dependencies..." -ForegroundColor Yellow
$pythonOutput = python -c "import prism" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Python dependencies (one-time)..." -ForegroundColor Yellow
    pip install -r local-companion/requirements.txt
}

# Start Python companion server in background
Write-Host "🐍 Starting Python companion on port 8765..." -ForegroundColor Green
Start-Process python -ArgumentList "local-companion/server.py" -WindowStyle Hidden

# Wait a moment for Python to start
Start-Sleep -Seconds 3

# Start Next.js frontend
Write-Host "⚡ Starting Next.js frontend on port 3000..." -ForegroundColor Green
pnpm dev

Write-Host "✅ Both services running!" -ForegroundColor Cyan
Write-Host "Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend:   http://localhost:8765/api/health" -ForegroundColor Cyan