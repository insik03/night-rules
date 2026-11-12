param([switch]$Tests, [string[]]$Cases)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskExe=Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Binaries/Win64/NightRulesPrototype.exe'
$taskOut=Join-Path $taskRoot 'Art/Previews/StoryProps-v1'
New-Item -ItemType Directory -Force -Path $taskOut | Out-Null
$taskCases=if($Tests){@('NRStoryPropsTest','NRExperienceTest','NRInvestigationTest','NRComplaintLogTest','NRDemoTest','NRPresentationTest')}else{@('rules','rules-red','rules-reader','note','note-world','ledger-world','service_ledger','uv_guide')}
if($Cases){$taskCases=$Cases}
foreach($taskCase in $taskCases){
 $taskStart=Get-Date
 $taskFlag=if($Tests){'-'+$taskCase}else{'-NRStoryPreview='+$taskCase}
 $taskLog=Join-Path $taskRoot ('tools/output/story-'+$taskCase+'.log')
 $taskP=Start-Process -FilePath $taskExe -ArgumentList @($taskFlag,'-windowed','-ResX=1600','-ResY=1000','-unattended',('-abslog="'+$taskLog+'"')) -WindowStyle Hidden -PassThru
 if(!$taskP.WaitForExit(60000)){Stop-Process -Id $taskP.Id;throw ('Timeout '+$taskCase)}
 if($taskP.ExitCode -ne 0){throw ('Game failed '+$taskCase)}
 if($Tests){
  Select-String -LiteralPath $taskLog -Pattern 'NR_.*(FAIL|COMPLETE)' | ForEach-Object {$_.Line}
  if(!(Select-String -LiteralPath $taskLog -Pattern 'NR_\w+_COMPLETE failures=0') -or (Select-String -LiteralPath $taskLog -Pattern 'NR_\w+ FAIL ')){throw ('Failed '+$taskCase)}
 }else{
  $taskShot=Get-ChildItem (Join-Path $taskRoot 'Builds/Windows/NightRulesPrototype/Saved/Screenshots/Windows') -Filter '*.png' | Where-Object LastWriteTime -ge $taskStart | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if(!$taskShot){throw ('No capture '+$taskCase)}
  Copy-Item -LiteralPath $taskShot.FullName -Destination (Join-Path $taskOut ($taskCase+'.png'))
  Write-Output ('Captured '+$taskCase)
 }
}
