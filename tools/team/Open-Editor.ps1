param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$editor = Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
$project = Join-Path $repoRoot 'NightRulesPrototype/NightRulesPrototype.uproject'
$module = Join-Path $repoRoot 'NightRulesPrototype/Binaries/Win64/UnrealEditor-NightRulesPrototype.dll'
if (!(Test-Path -LiteralPath $editor)) { throw 'Unreal Editor not found. Pass the correct -EngineRoot.' }
if (!(Test-Path -LiteralPath $module)) { throw 'Build the Editor target first: tools/build.ps1 -EngineRoot <UE folder> (see docs/team-setup.md).' }
Start-Process -FilePath $editor -ArgumentList ('"' + $project + '"') -WorkingDirectory $repoRoot
