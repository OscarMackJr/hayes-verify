[CmdletBinding()]param([string]$EMSPath="C:\temp\standars\ems")
$ErrorActionPreference="Stop"
$out=Join-Path $EMSPath "generated\wave2\higher-scope-remediation.csv"
$row=[pscustomobject]@{
 control_id="EMS-CTRL-072"
 control_name="PDF/DOCX Generation Validation"
 scope="EMS"
 disposition="REMEDIATE"
 current_status="WARNING"
 remediation_reason="No controlled PDF or DOCX outputs detected."
 required_evidence="Controlled DOCX output; controlled PDF output; successful generation validation; retained provenance tying outputs to controlled source/release."
}
if(Test-Path $out){
 $existing=Import-Csv $out
 $existing=@($existing|Where-Object control_id -ne "EMS-CTRL-072")
 @($existing+$row)|Export-Csv $out -NoTypeInformation
}else{
 $row|Export-Csv $out -NoTypeInformation
}
Write-Host "CTRL-072 remediation recorded: $out" -ForegroundColor Green
