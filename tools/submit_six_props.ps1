$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '../Art/GeneratedProps/six-v1'
$root = [IO.Path]::GetFullPath($root)
$jobs = @(
    @{name='chair'; id='01a15f1a-f2c0-729a-a055-b1cf53db178a'; project=(Join-Path $root 'meshy_output/20261022_003621_chair_01a15f1a')},
    @{name='bedding'; id='01a15f1b-3aec-74df-b319-132b9ffa36ce'},
    @{name='sink'}, @{name='shower'}, @{name='slippers'}, @{name='books'}
)
$record = Join-Path $root 'jobs.json'
if (Test-Path -LiteralPath $record) { throw 'Submission record exists; inspect it and resume existing IDs instead of resubmitting.' }
$jobs | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $record -Encoding utf8
foreach ($job in $jobs) {
    if (!$job.id) {
        $out = & npm exec --yes --package=meshy-cli@0.4.0 -- meshy image-to-3d create --image-url (Join-Path $root "references/$($job.name).png") --model-type standard --should-texture true --enable-pbr true --texture-resolution 4k --target-formats glb --async --operation-id "haedam-six-v1-$($job.name)" --workspace $root --output-schema v1 --format json --no-update-check
        $exit = $LASTEXITCODE
        $out | Set-Content -LiteralPath (Join-Path $root "$($job.name)-submission.json") -Encoding utf8
        $parsed = ($out -join "`n") | ConvertFrom-Json
        if ($exit -ne 0 -or !$parsed.ok -or !$parsed.result.submission.task_id) { throw "Submission uncertain/failed: $($job.name). Inspect saved output, do not retry create." }
        $job.id = $parsed.result.submission.task_id
        $jobs | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $record -Encoding utf8
    }
    if (!$job.project) {
        $out = & npm exec --yes --package=meshy-cli@0.4.0 -- meshy project init --root (Join-Path $root 'meshy_output') --name $job.name --task-id $job.id --task-type image-to-3d --workspace $root --output-schema v1 --format json --no-update-check
        $parsed = ($out -join "`n") | ConvertFrom-Json
        if (!$parsed.ok) { throw "Project init failed for existing $($job.id); do not recreate task." }
        $job.project = $parsed.result.project_dir
        $jobs | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $record -Encoding utf8
    }
    Write-Output "$($job.name): $($job.id)"
}
