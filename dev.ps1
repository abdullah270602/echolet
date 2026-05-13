# ==========================================
# Echolet Development Server
# Starts backend, agent, and worker locally
# ==========================================
# Usage: .\dev.ps1 [all|backend|agent|worker]
# ==========================================

param(
    [string]$Service = "all"
)

$ErrorActionPreference = "Stop"
$ROOT_DIR = $PSScriptRoot

# Colors for output
function Write-Color($Message, $Color = "White") {
    Write-Host $Message -ForegroundColor $Color
}

# Load environment variables from .env file
function Load-EnvFile {
    $envFile = Join-Path $ROOT_DIR ".env"
    if (Test-Path $envFile) {
        Write-Color "[*] Loading environment from .env" "Cyan"
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                # Remove surrounding quotes if present
                $value = $value -replace '^["'']|["'']$', ''
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    } else {
        Write-Color "[!] No .env file found. Copy .env.example to .env" "Yellow"
        exit 1
    }
}

# Start a service in a new terminal window
function Start-Service($Name, $Path, $Command) {
    Write-Color "[+] Starting $Name..." "Green"

    $workDir = Join-Path $ROOT_DIR $Path

    # Build the command to run in new window
    $script = @"
Set-Location '$workDir'
Write-Host '=== $Name ===' -ForegroundColor Cyan
Write-Host 'Working directory:' (Get-Location) -ForegroundColor Gray
Write-Host ''
$Command
Write-Host ''
Write-Host 'Press any key to exit...' -ForegroundColor Yellow
`$null = `$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"@

    # Copy environment variables to new process
    $envVars = @()
    Get-ChildItem Env: | Where-Object {
        $_.Name -match '^(DATABASE_URL|LIVEKIT_|DEEPGRAM_|OPENROUTER_|INWORLD_|SQS_|AWS_|CLERK_|DAILY_)'
    } | ForEach-Object {
        $envVars += "`$env:$($_.Name) = '$($_.Value)'"
    }

    $fullScript = ($envVars -join "`n") + "`n" + $script
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($fullScript)
    $encoded = [Convert]::ToBase64String($bytes)

    Start-Process powershell -ArgumentList "-NoExit", "-EncodedCommand", $encoded
}

# Start backend (FastAPI)
function Start-Backend {
    Start-Service "Backend API" "backend" "uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
}

# Start agent (LiveKit Voice Agent)
function Start-Agent {
    Start-Service "Voice Agent" "agent" "uv run python agent.py dev"
}

# Start worker (SQS Consumer)
function Start-Worker {
    Start-Service "SQS Worker" "worker" "uv run python worker.py"
}

# Main
Write-Color ""
Write-Color "========================================" "Magenta"
Write-Color "   Echolet Development Environment" "Magenta"
Write-Color "========================================" "Magenta"
Write-Color ""

Load-EnvFile

switch ($Service.ToLower()) {
    "all" {
        Start-Backend
        Start-Sleep -Milliseconds 500
        Start-Agent
        Start-Sleep -Milliseconds 500
        Start-Worker
        Write-Color ""
        Write-Color "[✓] All services started in separate windows" "Green"
        Write-Color ""
        Write-Color "Services:" "Cyan"
        Write-Color "  Backend API:  http://localhost:8000" "White"
        Write-Color "  Agent:        LiveKit dev mode" "White"
        Write-Color "  Worker:       SQS polling" "White"
        Write-Color ""
        Write-Color "Close the terminal windows to stop services." "Yellow"
    }
    "backend" {
        Start-Backend
    }
    "agent" {
        Start-Agent
    }
    "worker" {
        Start-Worker
    }
    default {
        Write-Color "Unknown service: $Service" "Red"
        Write-Color "Usage: .\dev.ps1 [all|backend|agent|worker]" "Yellow"
        exit 1
    }
}
