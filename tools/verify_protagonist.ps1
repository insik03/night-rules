$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskSaved=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Saved'
$taskOut=Join-Path $taskRoot 'Art/Previews/Protagonist-v3'
New-Item -ItemType Directory -Force -Path $taskOut,(Join-Path $taskSaved 'Verification') | Out-Null
$started=Get-Date
& (Join-Path $PSScriptRoot 'verify_polish.ps1') -Checks @('NRProtagonistTest')
foreach($name in @('player_idle.png','player_walk.png','player_run.png','player_crouch.png')) {
    $file=Get-Item -LiteralPath (Join-Path $taskSaved ('Verification/'+$name))
    if($file.LastWriteTime -lt $started){throw ('Stale player capture: '+$name)}
    $bytes=[IO.File]::ReadAllBytes($file.FullName)
    if($bytes[0] -ne 137 -or $bytes[1] -ne 80){throw ('Not a PNG: '+$name)}
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $taskOut $name)
}
$started=Get-Date
& (Join-Path $PSScriptRoot 'verify_polish.ps1') -Checks @('NROfficeCCTVTest')
$shot=Get-ChildItem (Join-Path $taskSaved 'Screenshots/Windows') -Filter '*.png' | Where-Object LastWriteTime -ge $started | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(!$shot){throw 'Fresh office CCTV capture missing'}
Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskOut 'office-cctv.png')
& (Join-Path $PSScriptRoot 'verify_polish.ps1') -Checks @('NRInvestigationTest','NRFeedbackTest')
@{status='passed';checks=@('NRProtagonistTest','NROfficeCCTVTest','NRInvestigationTest','NRFeedbackTest');verified_at=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $taskOut 'verification.json')
