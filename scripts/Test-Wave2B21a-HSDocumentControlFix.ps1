
[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$collector = Join-Path $EMSPath "scripts\collectors\higher-scope\Collect-HSDocumentControl.py"
$text = Get-Content $collector -Raw

$checks = [ordered]@{
    HasAuthoritativeDefinitionFiles = $text.Contains('authoritative_definition_files')
    HasDefinitionIds                = $text.Contains('definition_ids')
    HasReferenceIds                 = $text.Contains('reference_ids')
    HasDuplicateDefinitionIds       = $text.Contains('duplicate_definition_ids')
    UsesControlledIdsUnique         = $text.Contains('A["controlled_ids_unique"]')
    ExcludesGenerated               = $text.Contains('"\\generated\\"')
    ExcludesReleases                = ($text.Contains('"\\releases\\"') -or $text.Contains('"\\release\\"'))
    ExcludesBackups                 = $text.Contains('".bak"')
}

$rows = $checks.GetEnumerator() | ForEach-Object {
    [pscustomobject]@{ Check=$_.Key; Pass=[bool]$_.Value }
}

$rows | Format-Table -AutoSize

$failed=@($rows | Where-Object { -not $_.Pass })
if($failed.Count -gt 0){
    throw "Wave 2B.2.1a collector patch validation failed."
}

$py=Join-Path $EMSPath ".venv\Scripts\python.exe"
if(-not(Test-Path $py)){$py="python"}

& $py -m py_compile $collector
if($LASTEXITCODE-ne 0){
    throw "Patched collector Python syntax validation failed."
}

Write-Host "PASS: Wave 2B.2.1a collector correction is installed." -ForegroundColor Green
