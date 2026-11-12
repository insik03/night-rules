param([switch]$Tests,[string[]]$TestNames=@('NRArchitectureTest','NRMapTest','NRCCTVStackTest','NRDemoTest','NRChoice202Test','NRInvestigationTest'),[string[]]$ViewNames=@(),[ValidateSet('Architecture-v1','Architecture-v2','Architecture-v3','Architecture-v4','Architecture-v5','Architecture-v6','Architecture-v7','Architecture-v8','Architecture-v9')][string]$OutputFolder='Architecture-v2')
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskExe=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe'
$taskShots=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Saved/Screenshots/Windows'
$taskOut=Join-Path $taskRoot ('Art/Previews/'+$OutputFolder)
New-Item -ItemType Directory -Force -Path $taskOut | Out-Null
if($Tests) {
 foreach($taskTest in $TestNames) {
  $taskLog=Join-Path $taskRoot ('tools/output/'+$taskTest+'-architecture.log')
  $taskProc=Start-Process -FilePath $taskExe -ArgumentList @('-'+$taskTest,'-windowed','-ResX=960','-ResY=540','-unattended',('-abslog="'+$taskLog+'"')) -WindowStyle Hidden -PassThru
  if(!$taskProc.WaitForExit(190000)){Stop-Process -Id $taskProc.Id;throw ('Test timeout '+$taskTest)}
  Write-Output ($taskTest+' exit='+$taskProc.ExitCode)
  if(!(Test-Path -LiteralPath $taskLog)){throw ('No test log: '+$taskTest)}
  Select-String -LiteralPath $taskLog -Pattern 'COMPLETE| FAIL |ARCH_BLOCK|Missing architecture' | Select-Object -Last 14 | ForEach-Object {$_.Line}
  if($taskProc.ExitCode -ne 0 -or !(Select-String -LiteralPath $taskLog -Pattern 'NR_\w+_COMPLETE failures=0') -or (Select-String -LiteralPath $taskLog -Pattern 'NR_\w+ FAIL |NR_\w+_COMPLETE failures=[1-9]')){throw ('Test failed: '+$taskTest)}
 }
 exit
}
$taskViews=@(@('floor-1','-NRArchitectureFloor=1'),@('office-layout','-NRArchitectureFloor=1 -NRArchitectureDetail'),@('floor-2','-NRArchitectureFloor=2'),@('floor-3','-NRArchitectureFloor=3'),@('roof','-NRArchitectureFloor=4'),@('hall','-NRView=430,-135,410,0,0'),@('office-entry','-NRView=-60,-80,90,-5,-115'),@('office-inside','-NRView=-180,-820,90,-5,118 -NROpenDoors'),@('entrance','-NRView=-30,-150,90,0,85'),@('kitchen','-NRView=1055,-330,90,-7,-90 -NROpenDoors'),@('stair','-NRView=3610,-160,90,-4,-90'))
$taskViews+=,@('office-front','-NRView=-35,155,90,0,-90')
$taskViews+=,@('office-outward','-NRView=-310,-735,90,0,90')
$taskViews+=,@('office-corrected-inside','-NRView=65,-820,90,0,60')
$taskViews+=,@('office-corrected-outward','-NRView=220,-735,90,0,90')
$taskViews+=,@('door-front','-NRView=35,-280,90,0,-90')
$taskViews+=,@('door-back','-NRView=35,-710,90,0,90')
$taskViews+=,@('door-open','-NRView=-70,-290,90,0,-60 -NROpenDoors')
$taskViews+=,@('wallpaper-detail','-NRView=-100,-310,90,0,-90')
$taskViews+=,@('hall-1','-NRView=520,-145,90,0,20')
$taskViews+=,@('hall-3','-NRView=520,-145,730,0,20')
$taskViews+=,@('office-rules','-NRView=175,-670,90,0,-67')
$taskViews+=,@('office-ceiling-only','-NRView=65,-820,90,0,60 -ExecCmds="ShowFlag.SpotLights 0"')
$taskViews+=,@('cctv-desk','-NRDeskPreview')
$taskViews+=,@('cctv-panel','-NRCCTVPreview')
$taskViews+=,@('log-plan','-NRLogPlanPreview')
$taskViews+=,@('camera-mount','-NRView=95,-680,90,25,72')
foreach($taskView in $taskViews) {
 if($ViewNames.Count -gt 0 -and $taskView[0] -notin $ViewNames){continue}
 $taskStarted=Get-Date
 $taskLog=Join-Path $taskRoot ('tools/output/architecture-'+$taskView[0]+'.log')
 $taskProc=Start-Process -FilePath $taskExe -ArgumentList @($taskView[1],'-windowed','-ResX=1800','-ResY=1000','-unattended',('-abslog="'+$taskLog+'"')) -WindowStyle Hidden -PassThru
 if(!$taskProc.WaitForExit(45000)){Stop-Process -Id $taskProc.Id;throw ('Capture timeout '+$taskView[0])}
 if($taskProc.ExitCode -ne 0){throw ('Game failed '+$taskView[0])}
 $taskShot=Get-ChildItem $taskShots -Filter '*.png' | Where-Object LastWriteTime -ge $taskStarted | Sort-Object LastWriteTime -Descending | Select-Object -First 1
 if(!$taskShot){throw ('No screenshot '+$taskView[0])}
 Copy-Item -LiteralPath $taskShot.FullName -Destination (Join-Path $taskOut ($taskView[0]+'.png'))
 Write-Output ('Captured '+$taskView[0])
}
