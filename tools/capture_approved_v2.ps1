param([string]$ProjectRoot)
$ErrorActionPreference='Stop'
$taskExe=Join-Path $ProjectRoot 'Builds/Windows/NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe'
$taskOut=Join-Path $ProjectRoot 'Art/GeneratedProps/approved-v2/captures'
$taskShots=Join-Path $ProjectRoot 'Builds/Windows/NightRulesPrototype/Saved/Screenshots/Windows'
New-Item -ItemType Directory -Path $taskOut -Force | Out-Null
foreach($taskView in @(@('toolbox','-NRView=-235,-620,90,-38,-68'),@('upper-window','-NRView=-11,40,410,0,90'))) {
 $taskStarted=Get-Date
 $taskLog=Join-Path $ProjectRoot ('tools/output/capture-approved-'+$taskView[0]+'.log')
 $taskProc=Start-Process -FilePath $taskExe -ArgumentList @($taskView[1],'-windowed','-ResX=1440','-ResY=900','-unattended',('-abslog="'+$taskLog+'"')) -WindowStyle Hidden -PassThru
 if(!$taskProc.WaitForExit(45000)){Stop-Process -Id $taskProc.Id;throw 'Capture timeout'}
 if($taskProc.ExitCode -ne 0){throw 'Capture failed'}
 $taskShot=Get-ChildItem $taskShots -Filter '*.png' | Where-Object LastWriteTime -ge $taskStarted | Sort-Object LastWriteTime -Descending | Select-Object -First 1
 if(!$taskShot){throw 'No new capture'}
 Copy-Item -LiteralPath $taskShot.FullName -Destination (Join-Path $taskOut ($taskView[0]+'.png'))
 Write-Output ('Captured '+$taskView[0])
}
