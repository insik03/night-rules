$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskExe=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype.exe'
if(!(Test-Path -LiteralPath $taskExe)){throw 'Package the game before launching the final night.'}
Start-Process -FilePath $taskExe -WorkingDirectory (Split-Path $taskExe) -ArgumentList @('-NRFinale','-windowed','-ResX=1600','-ResY=900') -WindowStyle Hidden
