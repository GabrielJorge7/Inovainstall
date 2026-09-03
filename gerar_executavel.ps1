$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath "$projectRoot\inovainstall" `
    --workpath "$projectRoot\build_atualizado" `
    "$projectRoot\InovaInstall.spec"

$executable = Join-Path $projectRoot "inovainstall\InovaInstall.exe"
if (-not (Test-Path $executable)) {
    throw "O executável não foi gerado: $executable"
}

Write-Host "Executável atualizado: $executable"