$ErrorActionPreference = "Stop"

$downloadUrl = "https://github.com/GabrielJorge7/Inovainstall/raw/refs/heads/main/inovainstall/InovaInstall.exe"
$distributionDirectory = Join-Path $PSScriptRoot "inovainstall"
$localExe = Join-Path $distributionDirectory "InovaInstall.exe"
$temporaryExe = Join-Path $env:TEMP ("InovaInstall-" + [Guid]::NewGuid() + ".exe")

try {
    New-Item -ItemType Directory -Path $distributionDirectory -Force | Out-Null
    Write-Host "Baixando a versão mais recente do InovaInstall..."
    $cacheBustedUrl = "$downloadUrl?download=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
    Invoke-WebRequest `
        -Uri $cacheBustedUrl `
        -Headers @{ "Cache-Control" = "no-cache" } `
        -OutFile $temporaryExe `
        -UseBasicParsing

    if (-not (Test-Path $temporaryExe) -or (Get-Item $temporaryExe).Length -lt 1MB) {
        throw "O download do executável não foi concluído corretamente."
    }

    Move-Item -Path $temporaryExe -Destination $localExe -Force
    Write-Host "Iniciando o InovaInstall..."
    Write-Host "Arquivo atualizado: $localExe"
    $process = Start-Process -FilePath $localExe -PassThru
    $process.WaitForExit()
}
catch {
    Write-Error "Não foi possível baixar ou iniciar o InovaInstall: $($_.Exception.Message)"
    exit 1
}
finally {
    if (Test-Path $temporaryExe) {
        Remove-Item $temporaryExe -Force -ErrorAction SilentlyContinue
    }
}