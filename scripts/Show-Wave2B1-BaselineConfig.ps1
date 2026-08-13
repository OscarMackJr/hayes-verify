[CmdletBinding()]
param([string]$EMSPath = "C:\temp\standars\ems")

$runner = Join-Path $EMSPath "scripts\Run-Wave2B1-Inheritance.ps1"

Write-Host "Wave 2B.1 runner parameter / baseline lines:" -ForegroundColor Cyan

Select-String `
    -Path $runner `
    -Pattern 'param\(','EMSPath','Pass45','wave1-input','effective_compliance_postpolicy' |
    Select-Object LineNumber,Line |
    Format-Table -Wrap -AutoSize
