[CmdletBinding()]
param([string]$EMSPath="C:\temp\standars\ems")

$ErrorActionPreference="Stop"

$target = Join-Path $EMSPath "scripts\Generate-ControlledDocuments.py"
if(-not(Test-Path $target)){ throw "Generator not found: $target" }

$backup="$target.pre-2c1a-runtime-hotfix.bak"
Copy-Item $target $backup -Force

$text=Get-Content $target -Raw

# Replace PATH-only LibreOffice lookup with environment-aware lookup.
$old='libreoffice = shutil.which("libreoffice") or shutil.which("soffice")'
$new=@'
libreoffice = os.environ.get("EMS_SOFFICE") or shutil.which("soffice") or shutil.which("libreoffice")
if libreoffice:
    libreoffice = str(Path(libreoffice))
'@

if(-not $text.Contains($old)){
    Copy-Item $backup $target -Force
    throw "Expected LibreOffice lookup not found; original restored."
}

$text=$text.Replace($old,$new)
Set-Content $target $text -Encoding UTF8

$python=$null
if($env:VIRTUAL_ENV){
    $candidate=Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if(Test-Path $candidate){$python=$candidate}
}
if(-not $python){
    $cmd=Get-Command python -ErrorAction SilentlyContinue
    if($cmd){$python=$cmd.Source}
}
if(-not $python){ throw "Unable to locate Python for syntax validation." }

& $python -m py_compile $target
if($LASTEXITCODE-ne 0){
    Copy-Item $backup $target -Force
    throw "Patched generator failed Python syntax validation; original restored."
}

Write-Host "PASS: Generate-ControlledDocuments.py patched for explicit soffice runtime." -ForegroundColor Green
