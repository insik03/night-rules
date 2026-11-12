$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$started=Get-Date
& (Join-Path $PSScriptRoot 'verify_polish.ps1') -Checks @('NROfficeCCTVTest')
$shot=Get-ChildItem (Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Saved/Screenshots/Windows') -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(!$shot -or $shot.LastWriteTime -lt $started){throw 'Fresh office CCTV screenshot missing'}
Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskRoot 'Art/Previews/cctv-office-player.png')
& (Join-Path $PSScriptRoot 'verify_polish.ps1') -Checks @('NRExperienceTest','NRInvestigationTest')
