$ErrorActionPreference = "Stop"

$downloadUrl = "https://github.com/GabrielJorge7/Inovainstall/raw/refs/heads/main/inovainstall/InovaInstall.exe"
$temporaryExe = Join-Path $env:TEMP ("InovaInstall-" + [Guid]::NewGuid() + ".exe")

try {
    Write-Host "Baixando a versão mais recente do InovaInstall..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $temporaryExe -UseBasicParsing

    if (-not (Test-Path $temporaryExe) -or (Get-Item $temporaryExe).Length -lt 1MB) {
        throw "O download do executável não foi concluído corretamente."
    }

    Write-Host "Iniciando o InovaInstall..."
    $process = Start-Process -FilePath $temporaryExe -PassThru
    $process.WaitForExit()
}
finally {
    if (Test-Path $temporaryExe) {
        Remove-Item $temporaryExe -Force -ErrorAction SilentlyContinue
    }
}