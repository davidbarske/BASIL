$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Write-Step([string]$s) {
    Write-Host ""
    Write-Host "== $s" -ForegroundColor Cyan
}

function Find-Python312 {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) {
            try {
                $v = & $p -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
                if ($v -eq "3.12") { return $p }
            } catch {}
        }
    }
    try {
        $p = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null).Trim()
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    } catch {}
    return $null
}

function Invoke-Native([string]$exe, [string[]]$args, [switch]$AllowFailure) {
    $global:LASTEXITCODE = 0
    & $exe @args 2>&1 | ForEach-Object { Write-Host $_.ToString() }
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    if ($code -ne 0 -and -not $AllowFailure) {
        throw "Command failed with exit code ${code}: $exe $($args -join ' ')"
    }
    return [int]$code
}

Write-Host ""
Write-Host "BASIL BRITISH ANCHOR AUDITION v0.1 - SETUP" -ForegroundColor Green

Write-Step "1/4 Python 3.12"
$python = Find-Python312
if (-not $python) {
    throw "Python 3.12 was not found. BASIL Voice v0.3 should already have installed it."
}
Write-Host "Python: $python"

Write-Step "2/4 eSpeak-NG British phoneme engine"
$espeakCandidates = @(
    "$env:ProgramFiles\eSpeak NG\espeak-ng.exe",
    "${env:ProgramFiles(x86)}\eSpeak NG\espeak-ng.exe"
)
$espeak = $espeakCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1

if (-not $espeak) {
    $winget = (Get-Command winget.exe -ErrorAction SilentlyContinue).Source
    if (-not $winget) {
        throw "eSpeak-NG is absent and winget is unavailable."
    }
    Write-Host "Installing eSpeak-NG with winget..."
    $args = @(
        'install','--id','eSpeak-NG.eSpeak-NG','-e','--source','winget',
        '--silent','--accept-source-agreements','--accept-package-agreements',
        '--disable-interactivity'
    )
    Invoke-Native $winget $args | Out-Null
    Start-Sleep -Seconds 2
    $espeak = $espeakCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
}
if (-not $espeak) {
    throw "eSpeak-NG installation completed but espeak-ng.exe was not found."
}
$espeakDir = Split-Path -Parent $espeak
$env:PATH = "$espeakDir;$env:PATH"
Write-Host "eSpeak-NG: $espeak"
& $espeak --version | Select-Object -First 1

Write-Step "3/4 Isolated Kokoro environment"
$venv = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-Native $python @('-m','venv',$venv) | Out-Null
}
Invoke-Native $venvPython @('-m','pip','install','--upgrade','pip','setuptools','wheel') | Out-Null

$code = Invoke-Native $venvPython @('-m','pip','install','kokoro==0.9.4','soundfile','misaki[en]') -AllowFailure
if ($code -ne 0) {
    Write-Host ""
    Write-Warning "Combined install failed. Retrying in dependency-first order."
    Invoke-Native $venvPython @('-m','pip','install','misaki[en]','soundfile') | Out-Null
    Invoke-Native $venvPython @('-m','pip','install','kokoro==0.9.4') | Out-Null
}

Write-Step "4/4 Doctor"
$env:PATH = "$espeakDir;$env:PATH"
Invoke-Native $venvPython @('anchor_audition.py','doctor') | Out-Null

@"
SETUP_OK
python=$python
venv_python=$venvPython
espeak=$espeak
date=$(Get-Date -Format o)
"@ | Set-Content -LiteralPath (Join-Path $PSScriptRoot "SETUP_OK.txt") -Encoding UTF8

Write-Host ""
Write-Host "SETUP COMPLETE." -ForegroundColor Green
Write-Host "Next: RUN_ANCHOR_AUDITION.cmd"
