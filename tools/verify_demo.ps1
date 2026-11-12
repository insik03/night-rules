param([switch]$PreviewOnly)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
$checks=if($PreviewOnly){@('NRBlackoutPreview')}else{@('NRDemoTest','NRSmokeTest','NRChaseTest','NRBlackoutPreview')}
foreach($check in $checks){
    $log=Join-Path $taskRoot ('tools\output\'+$check+'.log'); $started=Get-Date
    # Audio remains enabled: the demo test validates real ambient audio components.
    $arguments=@("-$check",'-windowed','-ResX=1280','-ResY=720','-unattended',('-abslog="'+$log.Replace('\','/')+'"'))
    $p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
    if(!$p.WaitForExit(60000)){Stop-Process -Id $p.Id; throw "Timed out: $check"}
    if($p.ExitCode -ne 0){throw "Failed: $check ($($p.ExitCode))"}
    if($check.EndsWith('Test')){
        if(!(Select-String -LiteralPath $log -Pattern 'COMPLETE failures=0' -Quiet)){throw "Missing success: $check"}
        Get-Content $log | Select-String 'NR_DEMO |COMPLETE'
    }else{
        $shot=Get-ChildItem (Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Saved\Screenshots\Windows') -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if(!$shot -or $shot.LastWriteTime -lt $started){throw 'Fresh blackout screenshot missing'}
        Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskRoot 'Art\Previews\NRBlackoutPreview.png')
    }
}
