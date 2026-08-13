[CmdletBinding()]
param(
    [string]$EMSPath="C:\temp\standars\ems",
    [string]$Pass45="C:\temp\standars\Pass4_5"
)

Write-Host "Possible Wave 1 compliance inputs:" -ForegroundColor Cyan

@($EMSPath,$Pass45) |
    Where-Object { Test-Path $_ } |
    ForEach-Object {
        Get-ChildItem -Path $_ -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq "effective_compliance_postpolicy.csv" -or
                $_.Name -like "*Wave1*Baseline*.zip"
            } |
            Select-Object FullName,Length
    } |
    Sort-Object FullName |
    Format-Table -AutoSize
