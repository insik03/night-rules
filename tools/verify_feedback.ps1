param()
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
foreach($check in @('NRFeedbackTest','NRPausePreview','NRDrawerPreview','NRSubtitlePreview')) {
    $log=Join-Path $taskRoot ('tools\output\'+$check+'.log')
    $started=Get-Date
    $p=Start-Process -FilePath $exe -ArgumentList @("-$check",'-windowed','-ResX=1280','-ResY=720','-unattended',('-abslog="'+$log.Replace('\','/')+'"')) -WindowStyle Hidden -PassThru
    if(!$p.WaitForExit(60000)){Stop-Process -Id $p.Id; throw "Timed out: $check"}
    if($p.ExitCode -ne 0){Get-Content $log | Select-String 'NR_FEEDBACK'; throw "Failed: $check ($($p.ExitCode))"}
    if($check.EndsWith('Test')) {
        Get-Content $log | Select-String 'NR_FEEDBACK'
        if(!(Select-String -LiteralPath $log -Pattern 'NR_FEEDBACK_COMPLETE failures=0' -Quiet)){throw 'Missing feedback test success'}
    } else {
        $shot=Get-ChildItem (Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Saved\Screenshots\Windows') -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if(!$shot -or $shot.LastWriteTime -lt $started){throw 'Fresh pause screenshot missing'}
        Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskRoot ('Art\Previews\'+$check+'.png'))
    }
}
