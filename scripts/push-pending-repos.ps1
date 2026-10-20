# Run after GitHub "too many repositories" cooldown (~1 hour).
$ErrorActionPreference = 'Continue'
$Base = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Pending = @(
    @{ Dir = 'COSC 111 - Programming and Data Structures'; Slug = 'programming-data-structures-cosc111'; Desc = 'COSC 111 - Java data structures and OOP labs (EMU)' },
    @{ Dir = 'IA 329 - Policy Development Info Assurance'; Slug = 'ia329-policy-development-info-assurance'; Desc = 'IA 329 - Information assurance policy development coursework (EMU)' },
    @{ Dir = 'IA 244 - Administration of Computer Systems'; Slug = 'ia244-administration-computer-systems'; Desc = 'IA 244 - Computer systems administration labs and exams (EMU)' },
    @{ Dir = 'CET 151 - Intro to Computing in Engineering Tech'; Slug = 'cet-151-intro-computing-engineering-tech'; Desc = 'CET 151 - MATLAB, Excel, and C++ computing coursework (EMU)' }
)

foreach ($r in $Pending) {
    $dir = Join-Path $Base $r.Dir
    if (-not (Test-Path $dir)) { Write-Warning "Missing $dir"; continue }
    Set-Location $dir
    if (-not (Test-Path .git)) { git init | Out-Null }
    git add -A 2>$null
    if (git status --porcelain) { git commit -m 'Initial coursework archive (EMU)' | Out-Null }
    gh repo view "Jkbarros/$($r.Slug)" --json name -q .name 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        gh repo create "Jkbarros/$($r.Slug)" --public --description $r.Desc --source=. --remote=origin --push
    } else {
        if (-not (git remote get-url origin 2>$null)) { git remote add origin "https://github.com/Jkbarros/$($r.Slug).git" }
        git push -u origin master 2>$null
        if ($LASTEXITCODE -ne 0) { git push -u origin main }
    }
    Write-Host "Done $($r.Slug)"
    Start-Sleep -Seconds 120
}
