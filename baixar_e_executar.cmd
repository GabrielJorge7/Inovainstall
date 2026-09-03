@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0baixar_e_executar.ps1"
if errorlevel 1 (
    echo.
    echo Ocorreu um erro. A janela permanecera aberta para leitura.
    pause
)
endlocal