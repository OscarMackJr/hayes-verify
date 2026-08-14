$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = "C:\\temp\\standars\\hayes-verify\\.venv\\Scripts\\python.exe"
Set-Location $root
& $python "scripts/build_priority2_completion.py"
if ($LASTEXITCODE -ne 0) { throw "Priority-2 completion artifact build failed" }
