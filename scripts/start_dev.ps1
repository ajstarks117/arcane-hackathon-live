# Starts the ARCANE backend (port 8000) and the dashboard (port 5173) in two windows.
# Opens REAL pull requests unless ARCANE_DRY_RUN=1 is set in .env.
$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8 = "1"
# Skip Hugging Face network checks once the embedding model is cached (avoids ~2 min of timeouts offline).
if (Test-Path "$HOME/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2") { $env:HF_HUB_OFFLINE = "1" }
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root'; python -m uvicorn api.main:app --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$root\new_frontend'; `$env:PORT=5173; npm run dev"
Write-Host "Dashboard: http://localhost:5173   API docs: http://localhost:8000/docs"
