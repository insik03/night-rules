$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../Art/GeneratedProps/six-v1'))
$jobs=Get-Content -LiteralPath (Join-Path $root 'jobs.json') -Raw | ConvertFrom-Json
foreach($job in $jobs) {
    Write-Output "Waiting: $($job.name) / $($job.id)"
    $result=& npm exec --yes --package=meshy-cli@0.4.0 -- meshy image-to-3d wait $job.id --timeout 600 --project $job.project --stage generated --workspace $root --output-schema v1 --format json --no-update-check
    $exit=$LASTEXITCODE
    $result | Set-Content -LiteralPath (Join-Path $root "$($job.name)-result.json") -Encoding utf8
    if($exit -ne 0) { Write-Output "Wait exit $exit for $($job.name); retain task, do not recreate."; continue }
    $parsed=($result -join "`n") | ConvertFrom-Json
    if(!$parsed.ok){ Write-Output "Task not successful: $($job.name)"; continue }
    $dest=Join-Path $root $job.name
    New-Item -ItemType Directory -Force $dest | Out-Null
    $snapshot=Join-Path $job.project "task_$($job.id).json"
    $list=& npm exec --yes --package=meshy-cli@0.4.0 -- meshy download --task-json $snapshot --list --output-schema v1 --format json --no-update-check
    $list | Set-Content -LiteralPath (Join-Path $root "$($job.name)-assets.json") -Encoding utf8
    if(!(Test-Path -LiteralPath (Join-Path $dest 'model.glb'))) {
        $r=& npm exec --yes --package=meshy-cli@0.4.0 -- meshy download --task-json $snapshot --model-format glb --output (Join-Path $dest 'model.glb') --project $job.project --stage delivered --workspace $root --output-schema v1 --format json --no-update-check
        $r | Set-Content -LiteralPath (Join-Path $root "$($job.name)-download.json") -Encoding utf8
        Write-Output "Model download $($job.name): exit $LASTEXITCODE"
    }
    # The listing is recorded for agent inspection before selecting a thumbnail.
    Write-Output "Ready: $($job.name), snapshot $snapshot"
}
