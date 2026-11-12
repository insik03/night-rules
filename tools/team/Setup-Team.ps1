param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8',
    [switch]$SkipAssets,
    [switch]$SkipEnvironmentCheck
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location $repoRoot
try {
    if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows first.' }
    & git lfs version
    if ($LASTEXITCODE -ne 0) { throw 'Install Git LFS first.' }
    & git lfs install --local
    if ($LASTEXITCODE -ne 0) { throw 'Git LFS setup failed.' }
    & git config --local pull.ff only
    & git config --local push.default current
    & git config --local fetch.prune true
    & git config --local lfs.locksverify true
    if (!$SkipAssets) {
        & git lfs pull '--include=NightRulesPrototype/Content/**' '--exclude='
        if ($LASTEXITCODE -ne 0) { throw 'Game asset download failed. Check access and LFS quota.' }
        $missing = @(Get-ChildItem NightRulesPrototype/Content -Recurse -File | Where-Object {
            $_.Length -lt 1024 -and $_.Extension -in '.uasset','.umap','.ttf' -and
            (Get-Content -LiteralPath $_.FullName -TotalCount 1) -eq 'version https://git-lfs.github.com/spec/v1'
        })
        if ($missing.Count) { throw ("LFS pointers remain: " + $missing.Count) }
    }
    if (!$SkipEnvironmentCheck) {
        $versionFile = Join-Path $EngineRoot 'Engine/Build/Build.version'
        if (!(Test-Path -LiteralPath $versionFile)) { throw "Install Unreal Engine 5.8.3, or pass -EngineRoot to its folder." }
        $version = Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json
        if ($version.MajorVersion -ne 5 -or $version.MinorVersion -ne 8 -or $version.PatchVersion -ne 3) {
            throw 'The team uses Unreal Engine 5.8.3. Do not upgrade the project independently.'
        }
        $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
        if (!(Test-Path -LiteralPath $vswhere)) { throw 'Install Visual Studio 2022 C++ build tools.' }
        $vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if (!$vs) { throw 'Visual Studio C++ tools are missing.' }
        Write-Host ("C++ tools: " + $vs)
    }
    Write-Host 'Team setup complete. See docs/team-setup.md for the first build and asset locks.'
} finally { Pop-Location }
