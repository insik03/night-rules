param([int]$TimeoutSeconds=1800)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$exe=Join-Path $taskRoot 'Builds\Windows\NightRulesPrototype\Binaries\Win64\NightRulesPrototype.exe'
$log=Join-Path $taskRoot 'tools\output\NRDemoWalk.log'
$arguments=@('-NRDemoWalk','-windowed','-ResX=1280','-ResY=720','-unattended',('-abslog="'+$log.Replace('\','/')+'"'))
$p=Start-Process -FilePath $exe -ArgumentList $arguments -WindowStyle Hidden -PassThru
Write-Output "Known-route keyboard traversal PID=$($p.Id). This is not a blind first-play timing estimate."
$began=Get-Date
$last=''
while(!$p.WaitForExit(10000)) {
    if(Test-Path -LiteralPath $log) {
        $latest=(Get-Content -LiteralPath $log | Select-String 'NR_WALK PASS|NR_WALK_COMPLETE' | Select-Object -Last 1).Line
        if($latest -and $latest -ne $last) { Write-Output $latest; $last=$latest }
    }
    if(((Get-Date)-$began).TotalSeconds -gt $TimeoutSeconds) {
        Stop-Process -Id $p.Id
        throw "Keyboard traversal exceeded $TimeoutSeconds seconds. See $log"
    }
}
Get-Content -LiteralPath $log | Select-String 'NR_WALK_COMPLETE|NR_WALK obstruction'
if($p.ExitCode -ne 0 -or !(Select-String -LiteralPath $log -Pattern 'NR_WALK_COMPLETE failures=0' -Quiet)) {
    throw "Keyboard traversal failed. See $log"
}
