param(
 [Parameter(Mandatory=$true)][ValidateSet('O01','O03','O05','I01','I02','B01','K01','K06','R01','R04')][string]$Id,
 [Parameter(Mandatory=$true)][ValidateSet('Submit','Wait','Download')][string]$Action
)
$ErrorActionPreference='Stop'
$Root=Split-Path $PSScriptRoot -Parent
$Workspace=Join-Path $Root 'Art/CoreProps/v1'
$Runner='C:/Users/dbdls/AppData/Local/npm-cache/_npx/4bba5d0bb899d8c9/node_modules/meshy-cli/dist/index.js'
$Slugs=@{O01='caretaker-desk';O03='telephone';O05='cctv-monitor';I01='flashlight';I02='uv-cartridge';B01='room-door';K01='refrigerator';K06='round-table';R01='bare-bed-frame';R04='wardrobe'}
$Slug=$Slugs[$Id]
$Journal=Join-Path $Workspace 'meshy_output'
$StatePath=Join-Path $Journal ($Id+'-state.json')
function Invoke-Meshy([string[]]$Arguments,[string]$LogName) {
 $reply=& node $Runner @Arguments --output-schema v1 --format json --no-update-check
 $exit=$LASTEXITCODE
 $reply | Set-Content -LiteralPath (Join-Path $Journal ($Id+'-'+$LogName+'.json')) -Encoding UTF8
 try { $result=($reply -join [Environment]::NewLine) | ConvertFrom-Json } catch { throw "Uncertain CLI outcome for $Id $LogName. Inspect journal; never resubmit with a new operation ID." }
 if(-not $result.ok) { throw ($result.error | ConvertTo-Json -Depth 10 -Compress) }
 if($exit -ne 0) { Write-Warning "CLI exit $exit after valid successful response; recorded result retained." }
 return $result
}
if($Action -eq 'Submit') {
 $createPath=Join-Path $Journal ($Id+'-create.json')
 if(Test-Path -LiteralPath $createPath) {
  $create=Get-Content -LiteralPath $createPath -Raw | ConvertFrom-Json
  if(-not $create.ok -or -not $create.result.submission.task_id) {throw 'Existing submission outcome uncertain; manual audit required.'}
 } else {
  $ref=Join-Path $Workspace ('references/'+$Id+'-'+$Slug+'.png')
  if(-not (Test-Path -LiteralPath $ref)) {throw ('Missing approved reference '+$ref)}
  $create=Invoke-Meshy @('image-to-3d','create','--image-url',$ref,'--model-type','standard','--should-texture','true','--enable-pbr','true','--texture-resolution','4k','--ultra-mode','false','--target-formats','glb','--operation-id',('core10-'+$Id+'-v1'),'--async','--workspace',$Workspace) 'create'
 }
 $task=$create.result.submission.task_id
 if(Test-Path -LiteralPath $StatePath) {
  $state=Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
 } else {
  $existing=@(Get-ChildItem -LiteralPath $Journal -Directory | Where-Object {$_.Name -like ('*_'+$Id.ToLower()+'-'+$Slug+'_*')})
  if($existing.Count -eq 1) {$project=$existing[0].FullName}
  elseif($existing.Count -gt 1){throw 'Ambiguous existing project'}
  else {
   $init=Invoke-Meshy @('project','init','--root',$Journal,'--name',($Id+'-'+$Slug),'--task-id',$task,'--task-type','image-to-3d','--workspace',$Workspace) 'init'
   $project=$init.result.project_dir
  }
  $state=[pscustomobject]@{id=$Id;slug=$Slug;task_id=$task;resource='image-to-3d';project=$project}
  $state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8
 }
 [pscustomobject]@{id=$Id;task_id=$state.task_id;project=$state.project;status='accepted'} | ConvertTo-Json
 exit 0
}
$state=Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
if($Action -eq 'Wait') {
 $wait=Invoke-Meshy @('image-to-3d','wait',$state.task_id,'--timeout','600','--project',$state.project,'--stage','textured','--workspace',$Workspace) 'wait'
 [pscustomobject]@{id=$Id;task_id=$state.task_id;status=$wait.result.task.status;credits=$wait.result.task.consumed_credits} | ConvertTo-Json
 exit 0
}
if($Action -eq 'Download') {
 $out=Join-Path $Workspace ('models/'+$Id+'-'+$Slug)
 New-Item -ItemType Directory -Force -Path $out | Out-Null
 $snapshot=Join-Path $state.project ('task_'+$state.task_id+'.json')
 $taskData=Get-Content -LiteralPath (Join-Path $Journal ($Id+'-wait.json')) -Raw | ConvertFrom-Json
 if($taskData.result.task.status -ne 'SUCCEEDED'){throw 'Not a successful task'}
 foreach($kind in @('model','preview')){
  $target=Join-Path $out $(if($kind -eq 'model'){'source.glb'}else{'meshy-preview.png'})
  if(Test-Path -LiteralPath $target){Write-Output ('Keeping existing '+$target);continue}
  $args=@('download','--task-json',$snapshot,'--output',$target,'--project',$state.project,'--stage','delivered','--workspace',$Workspace)
  if($kind -eq 'model'){$args+=@('--model-format','glb')}else{$args+=@('--asset','thumbnail.primary')}
  $download=Invoke-Meshy $args ('download-'+$kind)
  [pscustomobject]@{id=$Id;kind=$kind;ok=$download.ok;path=$target} | ConvertTo-Json
 }
}
