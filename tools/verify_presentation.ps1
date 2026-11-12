param([switch]$Previews,[switch]$PreviewOnly)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskExe = Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
$taskChecks = @('NRPresentationTest','NRSmokeTest','NRKeyTest')
if ($PreviewOnly) { $taskChecks=@() }
if ($Previews -or $PreviewOnly) { $taskChecks += @('NRCCTVPreview','NRMessagePreview','NRDeskPreview') }
foreach ($taskCheck in $taskChecks) {
    $taskLog = Join-Path $taskRoot ('tools\output\' + $taskCheck + '.log')
    $taskStarted = Get-Date
    $taskArgs = @("-$taskCheck",'-windowed','-ResX=1280','-ResY=720','-unattended','-nosound',('-abslog="'+$taskLog.Replace('\','/')+'"'))
    $taskProcess = Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WindowStyle Hidden -PassThru
    if (!$taskProcess.WaitForExit(60000)) {
        Stop-Process -Id $taskProcess.Id
        throw "Timed out: $taskCheck"
    }
    if ($taskProcess.ExitCode -ne 0) { throw "Failed: $taskCheck ($($taskProcess.ExitCode)); see $taskLog" }
    if ($taskCheck.EndsWith('Test')) {
        if (!(Select-String -LiteralPath $taskLog -Pattern 'COMPLETE failures=0' -Quiet)) { throw "Missing completion: $taskCheck" }
        Get-Content -LiteralPath $taskLog | Select-String 'NR_PRESENTATION |COMPLETE'
    } else {
        $taskShotDir=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Saved\Screenshots\Windows'
        $taskShot=Get-ChildItem -LiteralPath $taskShotDir -Filter '*.png' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (!$taskShot -or $taskShot.LastWriteTime -lt $taskStarted) { throw "No fresh screenshot: $taskCheck" }
        $taskTarget=Join-Path $taskRoot ('Art\Previews\'+$taskCheck+'.png')
        Copy-Item -LiteralPath $taskShot.FullName -Destination $taskTarget
        Write-Output "CAPTURED $taskTarget"
    }
}
