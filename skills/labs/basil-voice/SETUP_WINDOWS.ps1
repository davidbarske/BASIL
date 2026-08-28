$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
Set-Location -LiteralPath $PSScriptRoot

Write-Host ""
Write-Host "BASIL VOICE CAPABILITY v0.3 - SELF-BOOTSTRAPPING SETUP" -ForegroundColor Cyan
Write-Host ""

function Step([string]$Text) {
    Write-Host ""
    Write-Host ("== " + $Text) -ForegroundColor Cyan
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [Parameter(Mandatory=$true)][string[]]$ArgumentList,
        [switch]$AllowFailure
    )

    # IMPORTANT: A PowerShell function emits everything written to its success
    # output stream. v0.2 allowed native stdout to escape from this function, so
    # callers assigning the result received [stdout lines..., exit_code] instead
    # of one integer. v0.3 routes native stdout/stderr to the host and returns
    # ONLY the real native exit code.
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $global:LASTEXITCODE = 0

        & $Exe @ArgumentList 2>&1 | ForEach-Object {
            Write-Host $_.ToString()
        }

        $code = $LASTEXITCODE
        if ($null -eq $code) { $code = 0 }
    } finally {
        $ErrorActionPreference = $saved
    }

    if ($code -ne 0 -and -not $AllowFailure) {
        throw "Command failed with exit code ${code}: $Exe $($ArgumentList -join ' ')"
    }

    return [int]$code
}

function Test-Python312([string]$Candidate) {
    if (-not $Candidate) { return $false }
    if (-not (Test-Path -LiteralPath $Candidate)) { return $false }
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $v = & $Candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        $code = $LASTEXITCODE
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $saved
    }
    return ($code -eq 0 -and (($v | Select-Object -First 1).Trim()) -eq "3.12")
}

function Find-Python312 {
    try {
        $saved = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $p = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        $code = $LASTEXITCODE
        $ErrorActionPreference = $saved
        if ($code -eq 0 -and $p) {
            $candidate = (($p | Select-Object -First 1).Trim())
            if (Test-Python312 $candidate) { return $candidate }
        }
    } catch {}

    try {
        $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($cmd -and (Test-Python312 $cmd.Source)) { return $cmd.Source }
    } catch {}

    $known = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe')
    )
    if (${env:ProgramFiles(x86)}) {
        $known += (Join-Path ${env:ProgramFiles(x86)} 'Python312\python.exe')
    }
    foreach ($candidate in $known) {
        if (Test-Python312 $candidate) { return $candidate }
    }

    $keys = @(
        'HKCU:\Software\Python\PythonCore\3.12\InstallPath',
        'HKLM:\Software\Python\PythonCore\3.12\InstallPath',
        'HKLM:\Software\WOW6432Node\Python\PythonCore\3.12\InstallPath'
    )
    foreach ($key in $keys) {
        try {
            $base = (Get-ItemProperty -LiteralPath $key -ErrorAction Stop).'(default)'
            if (-not $base) { $base = (Get-Item -LiteralPath $key -ErrorAction Stop).GetValue('') }
            if ($base) {
                $candidate = Join-Path $base 'python.exe'
                if (Test-Python312 $candidate) { return $candidate }
            }
        } catch {}
    }
    return $null
}

function Find-Winget {
    $cmd = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $alias = Join-Path $env:LOCALAPPDATA 'Microsoft\WindowsApps\winget.exe'
    if (Test-Path -LiteralPath $alias) { return $alias }
    return $null
}

function Get-NvidiaSmi {
    $cmd = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $fallback = Join-Path $env:WINDIR 'System32\nvidia-smi.exe'
    if (Test-Path -LiteralPath $fallback) { return $fallback }
    return $null
}

function Get-CudaWheelTag {
    $smi = Get-NvidiaSmi
    if (-not $smi) { return $null }
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $text = (& $smi 2>&1 | Out-String)
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $saved
    }
    if ($code -ne 0) { return $null }
    if ($text -match 'CUDA Version:\s*(\d+)\.(\d+)') {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -ge 13) { return 'cu130' }
        if ($major -eq 12 -and $minor -ge 8) { return 'cu128' }
        if ($major -eq 12 -and $minor -ge 6) { return 'cu126' }
        if ($major -eq 12 -and $minor -ge 4) { return 'cu124' }
    }
    return $null
}

Step '1/5  Host preflight'
$rootDrive = [IO.Path]::GetPathRoot($PSScriptRoot)
$driveName = $rootDrive.TrimEnd('\\').TrimEnd(':')
$drive = Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue
if ($drive) {
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    Write-Host "Free disk: $freeGB GB"
    if ($drive.Free -lt 12GB) { throw 'Less than 12 GB free disk space. Free space before continuing.' }
}

Step '2/5  Ensuring Python 3.12'
$pythonExe = Find-Python312
if (-not $pythonExe) {
    $winget = Find-Winget
    if (-not $winget) {
        throw 'Python 3.12 is absent and Windows Package Manager (winget) is unavailable. Install App Installer/winget, then rerun this setup.'
    }
    Write-Host 'Python 3.12 is not installed. Installing the official Python.Python.3.12 package for the current user...'
    $wgArgs = @(
        'install','--id','Python.Python.3.12','-e','--source','winget',
        '--scope','user','--silent','--accept-source-agreements','--accept-package-agreements',
        '--disable-interactivity'
    )
    $code = Invoke-NativeChecked -Exe $winget -ArgumentList $wgArgs -AllowFailure

    Start-Sleep -Seconds 2
    $pythonExe = Find-Python312

    if (-not $pythonExe -and $code -ne 0) {
        Write-Warning "Python is still not discoverable after the user-scope attempt (winget exit $code). Retrying with winget default scope."
        $wgArgs2 = @(
            'install','--id','Python.Python.3.12','-e','--source','winget',
            '--silent','--accept-source-agreements','--accept-package-agreements',
            '--disable-interactivity'
        )
        $code2 = Invoke-NativeChecked -Exe $winget -ArgumentList $wgArgs2 -AllowFailure
        Start-Sleep -Seconds 2
        $pythonExe = Find-Python312
        if (-not $pythonExe -and $code2 -ne 0) {
            throw "winget did not leave a usable Python 3.12 installation. First exit: $code; second exit: $code2. Return SETUP_DIAGNOSTICS.txt."
        }
    }

    if (-not $pythonExe) {
        throw 'winget completed but Python 3.12 could not be located or executed. Return SETUP_DIAGNOSTICS.txt.'
    }
    Write-Host "Python installed: $pythonExe" -ForegroundColor Green
} else {
    Write-Host "Python 3.12 found: $pythonExe"
}

Step '3/5  Creating isolated BASIL voice environment'
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath '.venv') {
    $validVenv = $false
    if (Test-Path -LiteralPath $venvPython) {
        try {
            $v = & $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            if ($LASTEXITCODE -eq 0 -and (($v | Select-Object -First 1).Trim()) -eq '3.12') { $validVenv = $true }
        } catch {}
    }
    if (-not $validVenv) {
        Write-Host 'Removing incomplete/incompatible local .venv...'
        Remove-Item -LiteralPath '.venv' -Recurse -Force
    }
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    Invoke-NativeChecked -Exe $pythonExe -ArgumentList @('-m','venv','.venv') | Out-Null
}
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'Virtual environment creation did not produce .venv\Scripts\python.exe.' }
Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','--upgrade','pip','setuptools','wheel') | Out-Null

Step '4/5  Installing BASIL voice runtime'
$cudaTag = Get-CudaWheelTag
if ($cudaTag) {
    Write-Host "NVIDIA CUDA-capable driver detected. Installing PyTorch GPU runtime: $cudaTag"
    $torchIndex = "https://download.pytorch.org/whl/$cudaTag"
    $torchCode = Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','--upgrade','torch','torchaudio','--index-url',$torchIndex) -AllowFailure
    if ($torchCode -ne 0) {
        Write-Warning "CUDA PyTorch install failed (exit $torchCode). Continuing with the standard dependency path; doctor will report whether CUDA is available."
    }
} else {
    Write-Host 'No supported NVIDIA CUDA runtime was detected. Installing standard PyTorch dependency path.'
}
Invoke-NativeChecked -Exe $venvPython -ArgumentList @('-m','pip','install','--prefer-binary','-r','requirements.txt') | Out-Null

Step '5/5  Runtime doctor'
$doctorCode = Invoke-NativeChecked -Exe $venvPython -ArgumentList @('basil_voice.py','doctor') -AllowFailure
if ($doctorCode -ne 0) {
    throw "BASIL voice doctor failed with exit code $doctorCode. Copy the visible output back into the BASIL chat."
}

Write-Host ""
Write-Host 'SETUP COMPLETE.' -ForegroundColor Green
Write-Host 'Next: double-click RUN_DESIGN_VOICE.cmd'
