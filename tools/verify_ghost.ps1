param([switch]$PreviewOnly)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$taskExe=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
$checks=if($PreviewOnly){@('NRGhostPreview')}else{@('NRGhostPreview','NRSmokeTest','NRChaseTest')}
foreach($check in $checks){
    $log=Join-Path $taskRoot ('tools\output\'+$check+'.log')
    $started=Get-Date
    $argsList=@("-$check",'-windowed','-ResX=1280','-ResY=720','-unattended','-nosound',('-abslog="'+$log.Replace('\','/')+'"'))
    $p=Start-Process -FilePath $taskExe -ArgumentList $argsList -WindowStyle Hidden -PassThru
    if(!$p.WaitForExit(60000)){Stop-Process -Id $p.Id;throw "Timed out: $check"}
    if($p.ExitCode -ne 0){throw "Process failed: $check"}
    if($check -eq 'NRGhostPreview'){
        if(!(Select-String -LiteralPath $log -Pattern 'GHOST_VISUAL_CHECK mesh=loaded animation=playing' -Quiet)){throw 'Ghost mesh or animation missing'}
        if(Select-String -LiteralPath $log -Pattern 'missing usage flag|fix material usage flag' -Quiet){throw 'Ghost skeletal material shader missing'}
        $shot=Get-ChildItem (Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Saved\Screenshots\Windows') -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if(!$shot -or $shot.LastWriteTime -lt $started){throw 'Fresh ghost screenshot missing'}
        Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskRoot 'Art\Previews\NRGhostPreview.png')
    }elseif(!(Select-String -LiteralPath $log -Pattern 'COMPLETE failures=0' -Quiet)){throw "Test failed: $check"}
    Write-Output "PASS $check"
}
