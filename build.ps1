<#
.SYNOPSIS
    Builds the Cloudygram Elyx plugin.

.DESCRIPTION
    Produces a source build (AST validated) using .venv and a compiled release
    using .venv311 (must be Python 3.11 to match the device runtime).
    Artifacts are written to builds/.

.PARAMETER Mode
    both (default), source, or release.

.PARAMETER Bootstrap
    Creates the .venv / .venv311 virtual environments and installs ElyxBuilder.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Mode source
    .\build.ps1 -Bootstrap
#>
[CmdletBinding()]
param(
    [ValidateSet('both', 'source', 'release')]
    [string]$Mode = 'both',

    [switch]$Bootstrap
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Write-Step([string]$Text) {
    Write-Host ''
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Ensure-Lib([string]$Venv) {
    $python = Join-Path $PSScriptRoot "$Venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        Write-Host "Creating $Venv ..." -ForegroundColor Yellow
        if ($Venv -eq '.venv311') {
            py -3.11 -m venv $Venv
        }
        else {
            python -m venv $Venv
        }
    }
    & $python -m pip install --upgrade ElyxBuilder | Out-Null
}

function Repair-CompileBug {
    # ElyxBuilder 0.6.3 imports "from cmds.obfuscate" instead of "elyb.cmds.obfuscate".
    $buildPy = Join-Path $PSScriptRoot '.venv311\Lib\site-packages\elyb\cmds\build.py'
    if (-not (Test-Path -LiteralPath $buildPy)) { return }
    $raw = Get-Content -Raw -LiteralPath $buildPy
    if ($raw -match 'from cmds\.obfuscate') {
        Set-Content -LiteralPath $buildPy -Value ($raw -replace 'from cmds\.obfuscate', 'from elyb.cmds.obfuscate') -NoNewline
        Write-Host 'Patched ElyxBuilder compile bug in .venv311' -ForegroundColor Yellow
    }
}

function Invoke-Build([string]$Venv, [string[]]$BuildArgs, [string]$Label) {
    $elyb = Join-Path $PSScriptRoot "$Venv\Scripts\elyb.exe"
    if (-not (Test-Path -LiteralPath $elyb)) {
        throw "Missing $Venv. Run: .\build.ps1 -Bootstrap"
    }
    Write-Step "$Label build ($Venv)"
    & $elyb @BuildArgs
    if ($LASTEXITCODE -ne 0) { throw "$Label build failed (exit code $LASTEXITCODE)." }
}

if ($Bootstrap) {
    Write-Step 'Bootstrapping virtual environments'
    Ensure-Lib '.venv'
    Ensure-Lib '.venv311'
}

if ($Mode -in @('both', 'source')) {
    Invoke-Build '.venv' @('build', '--ast', '--verbose', '--no-folder') 'Source (AST)'
}

if ($Mode -in @('both', 'release')) {
    Repair-CompileBug
    Invoke-Build '.venv311' @('build', '--compile', '2', '--verbose', '--no-folder') 'Release (compiled, Python 3.11)'
}

Write-Step 'Artifacts'
Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'builds') -Filter '*.eaf' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 6 |
    ForEach-Object { Write-Host ("  {0}  {1:N0} bytes  {2}" -f $_.Name, $_.Length, $_.LastWriteTime) }
