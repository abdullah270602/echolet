# ==========================================
# Echolet Development Setup
# Initializes virtual environments for all services
# ==========================================

$ErrorActionPreference = "Stop"
$ROOT_DIR = $PSScriptRoot

function Write-Color($Message, $Color = "White") {
    Write-Host $Message -ForegroundColor $Color
}

Write-Color ""
Write-Color "========================================" "Magenta"
Write-Color "   Echolet Development Setup" "Magenta"
Write-Color "========================================" "Magenta"
Write-Color ""

# Check if uv is installed
try {
    $null = Get-Command uv -ErrorAction Stop
    Write-Color "[✓] uv is installed" "Green"
} catch {
    Write-Color "[!] uv is not installed. Install it with:" "Red"
    Write-Color "    irm https://astral.sh/uv/install.ps1 | iex" "Yellow"
    exit 1
}

# Setup each service
$services = @("backend", "agent", "worker")

foreach ($service in $services) {
    $servicePath = Join-Path $ROOT_DIR $service
    Write-Color ""
    Write-Color "[*] Setting up $service..." "Cyan"

    Push-Location $servicePath
    try {
        # Sync dependencies
        Write-Color "    Installing dependencies..." "Gray"
        uv sync
        Write-Color "    [✓] $service ready" "Green"
    } finally {
        Pop-Location
    }
}

# Check for .env file
$envFile = Join-Path $ROOT_DIR ".env"
$envExample = Join-Path $ROOT_DIR ".env.example"

Write-Color ""
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Write-Color "[!] No .env file found. Creating from .env.example..." "Yellow"
        Copy-Item $envExample $envFile
        Write-Color "    [✓] Created .env - please fill in your values" "Green"
    } else {
        Write-Color "[!] No .env or .env.example found" "Red"
    }
} else {
    Write-Color "[✓] .env file exists" "Green"
}

Write-Color ""
Write-Color "========================================" "Magenta"
Write-Color "   Setup Complete!" "Green"
Write-Color "========================================" "Magenta"
Write-Color ""
Write-Color "Next steps:" "Cyan"
Write-Color "  1. Edit .env with your API keys" "White"
Write-Color "  2. Run: .\dev.ps1" "White"
Write-Color ""
