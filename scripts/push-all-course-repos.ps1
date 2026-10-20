$ErrorActionPreference = 'Continue'
$Base = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Skip = @('college-projects')

Get-ChildItem $Base -Directory | Where-Object { $Skip -notcontains $_.Name -and (Test-Path "$($_.FullName)\.git") } | ForEach-Object {
    Set-Location $_.FullName
    git add -A 2>$null
    if (-not (git status --porcelain)) {
        Write-Host "skip (clean): $($_.Name)"
        return
    }
    git commit -m "Add archive index and README encoding fixes" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "skip (commit): $($_.Name)"
        return
    }
    git push -u origin master 2>$null
    if ($LASTEXITCODE -ne 0) { git push -u origin main 2>$null }
    if ($LASTEXITCODE -ne 0) { git push 2>$null }
    Write-Host "pushed: $($_.Name)"
}
