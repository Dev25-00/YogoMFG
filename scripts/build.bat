@echo off
rem Construit dist\YogoMFG\YogoMFG.exe (onedir). Inclut mod\ et assets\.
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --windowed --name YogoMFG ^
  --icon assets\yogo.ico ^
  --add-data "mod;mod" ^
  --add-data "assets;assets" ^
  --collect-all customtkinter ^
  yogomfg.py
echo.
echo Build fini: dist\YogoMFG\YogoMFG.exe
