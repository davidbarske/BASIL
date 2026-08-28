$ErrorActionPreference = "Stop"

$setupPath = Join-Path $PSScriptRoot "SETUP_WINDOWS.ps1"
$tokens = $null
$errors = $null

[System.Management.Automation.Language.Parser]::ParseFile(
    $setupPath,
    [ref]$tokens,
    [ref]$errors
) | Out-Null

if ($errors -and $errors.Count -gt 0) {
    Write-Host ""
    Write-Host "PowerShell parser check FAILED." -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host $err.Message -ForegroundColor Red
        if ($err.Extent) {
            Write-Host ("Line {0}, column {1}" -f $err.Extent.StartLineNumber, $err.Extent.StartColumnNumber) -ForegroundColor DarkRed
        }
    }
    exit 9
}

Write-Host "Parser check passed." -ForegroundColor Green
exit 0
