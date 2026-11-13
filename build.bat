@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
REM 用法：把原版 ROM 拖到這個檔案上，或在命令列執行 build.bat "Reigen Doushi (Japan).nes"
if "%~1"=="" goto usage
python -m pip install -q -r "%~dp0requirements.txt"
python "%~dp0build.py" %*
pause
exit /b
:usage
echo 請把原版 ROM「Reigen Doushi ^(Japan^).nes」拖到 build.bat 上，或執行：build.bat 原版ROM.nes
pause
exit /b 1
