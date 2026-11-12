param([string[]]$Views=@('intro','report','307','escape','TRUE','RED','BLACK'))
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskExe=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe'
$taskShots=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Saved/Screenshots/Windows'
$taskOut=Join-Path $taskRoot 'Art/Previews/Endings-v1'
New-Item -ItemType Directory -Force -Path $taskOut | Out-Null
foreach($taskView in $Views) {
 $taskStarted=Get-Date
 $taskLog=Join-Path $taskRoot ('tools/output/ending-'+$taskView+'.log')
 $taskProc=Start-Process -FilePath $taskExe -ArgumentList @('-NRFinalePreview='+$taskView,'-windowed','-ResX=1800','-ResY=1000','-unattended',('-abslog="'+$taskLog+'"')) -WindowStyle Hidden -PassThru
 if(!$taskProc.WaitForExit(65000)){Stop-Process -Id $taskProc.Id;throw ('Capture timeout '+$taskView)}
 if($taskProc.ExitCode -ne 0){throw ('Capture failed '+$taskView)}
 $taskShot=Get-ChildItem -LiteralPath $taskShots -Filter '*.png' | Where-Object LastWriteTime -ge $taskStarted | Sort-Object LastWriteTime -Descending | Select-Object -First 1
 if(!$taskShot){throw ('No screenshot '+$taskView)}
 Copy-Item -LiteralPath $taskShot.FullName -Destination (Join-Path $taskOut ($taskView+'.png'))
 Write-Output ('Captured '+$taskView)
}
