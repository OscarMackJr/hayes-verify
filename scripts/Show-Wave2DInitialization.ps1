[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")
$root=(Resolve-Path $EMSPath).Path

foreach($pair in @(
    @{Label="Wave 2D initialization";Path="generated\wave2d\initialization_record.json"},
    @{Label="Wave 2D scope";Path="registry\wave2d\scope.json"},
    @{Label="Wave 2D population";Path="registry\wave2d\population.json"}
)){
    Write-Host "`n$($pair.Label):" -ForegroundColor Cyan
    $p=Join-Path $root $pair.Path
    if(Test-Path $p){Get-Content $p}else{Write-Host "NOT YET GENERATED" -ForegroundColor Yellow}
}

Write-Host "`nGit status:" -ForegroundColor Cyan
git -C $root status --short
