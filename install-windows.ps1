<#
.SYNOPSIS
  Installs PiperScribe from this checkout on Windows.

.DESCRIPTION
  Creates .venv if it is missing, installs the package in editable mode, and
  checks the tools PiperScribe calls out to. Safe to re-run.

  Works with Windows PowerShell 5.1 and PowerShell 7. Keep this file ASCII-only:
  5.1 reads BOM-less files as ANSI, so non-ASCII characters break parsing.

.PARAMETER Dev
  Also install the dev extras (pytest, ruff, mypy).

.EXAMPLE
  .\install-windows.ps1

.EXAMPLE
  .\install-windows.ps1 -Dev
#>
[CmdletBinding()]
param(
    [switch]$Dev
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$Extras = if ($Dev) { 'importers,dev' } else { 'importers' }

function Write-Info($msg) { Write-Host "[install] $msg" }
function Write-Warn($msg) { Write-Host "[install] WARNING: $msg" -ForegroundColor Yellow }

# Run a native command and fail if it returns a non-zero exit code.
# Windows PowerShell 5.1 does not check native exit codes on its own.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Exe $($Arguments -join ' ')"
    }
}

# True if the interpreter started with the given prefix is Python 3.10 or newer.
# The Microsoft Store "python" stub fails here, so it is skipped.
function Test-SupportedPython {
    param([string]$Exe, [string[]]$Prefix)
    try {
        & $Exe @Prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Find-Python {
    $candidates = @(
        @{ Exe = 'py';      Prefix = @('-3') },
        @{ Exe = 'python';  Prefix = @() },
        @{ Exe = 'python3'; Prefix = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
        if (Test-SupportedPython -Exe $c.Exe -Prefix $c.Prefix) {
            return $c
        }
    }
    return $null
}

try {
    $VenvDir = Join-Path $PSScriptRoot '.venv'
    $VenvPy  = Join-Path $VenvDir 'Scripts\python.exe'
    $HasUv   = [bool](Get-Command uv -ErrorAction SilentlyContinue)

    Write-Info '[1/4] Python environment'
    if (Test-Path -LiteralPath $VenvPy) {
        Write-Info 'Reusing existing .venv'
    } elseif ($HasUv) {
        Write-Info 'Creating .venv with uv'
        Invoke-Native 'uv' @('venv', '--python', '>=3.10', $VenvDir)
    } else {
        $py = Find-Python
        if (-not $py) {
            throw 'Python 3.10+ not found. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), or install uv from https://docs.astral.sh/uv/'
        }
        Write-Info "Creating .venv with $($py.Exe) $($py.Prefix -join ' ')"
        Invoke-Native $py.Exe (@($py.Prefix) + @('-m', 'venv', $VenvDir))
    }

    Write-Info "[2/4] Installing PiperScribe (editable, extras: $Extras)"
    if ($HasUv) {
        Invoke-Native 'uv' @('pip', 'install', '--python', $VenvPy, '-e', ".[$Extras]")
    } else {
        Invoke-Native $VenvPy @('-m', 'pip', 'install', '--upgrade', 'pip')
        Invoke-Native $VenvPy @('-m', 'pip', 'install', '-e', ".[$Extras]")
    }

    Write-Info '[3/4] Checking tools'
    $piper = Get-Command piper -ErrorAction SilentlyContinue
    if ($piper) {
        Write-Info "Found piper: $($piper.Source)"
    } else {
        Write-Warn "'piper' is not on PATH. The app opens without it, but Preview and Export need it."
        Write-Warn 'Install Piper from https://github.com/rhasspy/piper/releases and add its folder to PATH.'
    }
    Write-Warn 'Known limitation: the main-window Preview button and the Voice tab Test button play audio through aplay, which Windows does not have. Export WAV and Document Settings > Test Voice still work.'

    $VoiceDir = Join-Path $HOME '.local\share\piper\voices'
    New-Item -ItemType Directory -Force -Path $VoiceDir | Out-Null
    Write-Info "Voice folder: $VoiceDir"

    Write-Info '[4/4] Verifying the install'
    Invoke-Native $VenvPy @('-c', 'import PySide6, piperscribe.ui.main_window')

    Write-Info 'Done. Start PiperScribe with:'
    Write-Host '  .\.venv\Scripts\piperscribe.exe'
    exit 0
} catch {
    Write-Host "[install] ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
