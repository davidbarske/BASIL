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

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Exe,

        [Parameter(Mandatory=$false)]
        [string[]]$ArgumentList = @(),

        [switch]$AllowFailure
    )

    $global:LASTEXITCODE = 0
    $nativeOutput = @()
    $code = 0
    $oldErrorActionPreference = $ErrorActionPreference

    try {
        # Windows PowerShell 5.1 wraps redirected native stderr as ErrorRecord objects.
        # With script-wide ErrorActionPreference=Stop, ordinary native diagnostics can
        # otherwise become terminating PowerShell errors. Temporarily allow them, capture
        # both streams, then treat the native process exit code as authority.
        $ErrorActionPreference = "Continue"
        $nativeOutput = @(& $Exe @ArgumentList 2>&1)
        $code = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }

    foreach ($line in $nativeOutput) {
        if ($null -ne $line) {
            Write-Host $line.ToString()
        }
    }

    if ($null -eq $code) { $code = 0 }

    if ($code -ne 0 -and -not $AllowFailure) {
        throw "Command failed with exit code ${code}: $Exe $($ArgumentList -join ' ')"
    }

    # Return exactly one scalar integer. Do not leak native stdout/stderr into the
    # PowerShell success pipeline.
    return [int]$code
}

Write-Host ""
Write-Host "BASIL BRITISH ANCHOR AUDITION v0.3 - SETUP" -ForegroundColor Green

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
    $wingetArgs = @(
        'install','--id','eSpeak-NG.eSpeak-NG','-e','--source','winget',
        '--silent','--accept-source-agreements','--accept-package-agreements',
        '--disable-interactivity'
    )
    Invoke-NativeChecked -Exe $winget -ArgumentList $wingetArgs | Out-Null
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
    Invoke-NativeChecked -Exe $python -ArgumentList @('-m','venv',$venv) | Out-Null
}
Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','--upgrade','pip','setuptools','wheel') | Out-Null

# Official Kokoro release line. Install British-English G2P explicitly as well.
$code = Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','kokoro==0.9.4','soundfile','misaki[en]') -AllowFailure
if ($code -ne 0) {
    Write-Host ""
    Write-Warning "Combined install failed. Retrying in dependency-first order."
    Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','misaki[en]','soundfile') | Out-Null
    Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','kokoro==0.9.4') | Out-Null
}

Write-Step "4/4 Doctor"
$env:PATH = "$espeakDir;$env:PATH"
Invoke-NativeChecked -Exe $venvPython -ArgumentList @('anchor_audition.py','doctor') | Out-Null

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
