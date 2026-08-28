$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
Write-Host ""; Write-Host "BASIL VOICE CAPABILITY v0.1 - SETUP" -ForegroundColor Cyan; Write-Host ""
$mode=$null
try { & py -3.12 -c "import sys; print(sys.executable)" 2>$null | Out-Null; if($LASTEXITCODE -eq 0){$mode='py'} } catch {}
if(-not $mode){ try { $v=& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null; if($LASTEXITCODE -eq 0 -and $v -eq '3.12'){$mode='python'} } catch {} }
if(-not $mode){ Write-Host "Python 3.12 was not found." -ForegroundColor Yellow; Write-Host "Install it, then run again. Suggested: winget install Python.Python.3.12"; exit 2 }
$root=[IO.Path]::GetPathRoot($PSScriptRoot); $driveName=$root.TrimEnd('\').TrimEnd(':'); $drive=Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue
if($drive -and $drive.Free -lt 12GB){ throw 'Less than 12 GB free disk space. Free space before downloading the TTS models.' }
if(-not (Test-Path '.venv')){ if($mode -eq 'py'){ & py -3.12 -m venv .venv } else { & python -m venv .venv } }
$py=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt
& $py basil_voice.py doctor
Write-Host ""; Write-Host "SETUP COMPLETE." -ForegroundColor Green; Write-Host "Next: run RUN_DESIGN_VOICE.cmd"
