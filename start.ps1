$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = if (Test-Path -LiteralPath '.venv/Scripts/python.exe') { (Resolve-Path '.venv/Scripts/python.exe').Path } else { 'python' }
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) {
    Push-Location frontend
    try {
        $taskNode = (Get-Command node -ErrorAction SilentlyContinue).Source
        if (-not $taskNode) { $taskNode = Join-Path $env:ProgramFiles 'nodejs/node.exe' }
        & $taskNode node_modules/vite/bin/vite.js build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed; install frontend dependencies first' }
        & $taskNode scripts/build-sw.mjs
        if ($LASTEXITCODE -ne 0) { throw 'Offline cache build failed' }
    } finally { Pop-Location }
}
Write-Host 'Open http://127.0.0.1:8000. Keep this terminal open. Press Ctrl+C to stop.'
Set-Location backend
& $taskPython -m uvicorn main:app --host 127.0.0.1 --port 8000
