param()
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
foreach($check in @('NRExperienceTest','NRPresentationTest','NRFeedbackTest','NRSmokeTest','NRRulesPreview','NRSettingsPreview','NRSubtitlePreview','NRReplayPreview','NRDeskPreview')) {
    $log=Join-Path $taskRoot ('tools\output\'+$check+'.log')
    $started=Get-Date
    $p=Start-Process -FilePath $exe -ArgumentList @("-$check",'-windowed','-ResX=1280','-ResY=720','-unattended',('-abslog="'+$log.Replace('\','/')+'"')) -WindowStyle Hidden -PassThru
    if(!$p.WaitForExit(60000)){Stop-Process -Id $p.Id; throw "Timed out: $check"}
    if($p.ExitCode -ne 0){Get-Content $log | Select-String 'NR_.*(FAIL|COMPLETE)'; throw "Failed: $check ($($p.ExitCode))"}
    if($check.EndsWith('Test')) {
        Get-Content $log | Select-String '(NR_EXPERIENCE|NR_PRESENTATION|NR_FEEDBACK)'
        if(!(Select-String -LiteralPath $log -Pattern 'COMPLETE failures=0' -Quiet)){throw "Missing test success: $check"}
    } else {
        $shot=Get-ChildItem (Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Saved\Screenshots\Windows') -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if(!$shot -or $shot.LastWriteTime -lt $started){throw 'Fresh screenshot missing'}
        Copy-Item -LiteralPath $shot.FullName -Destination (Join-Path $taskRoot ('Art\Previews\'+$check+'.png'))
    }
}
