@echo off
rem Construit dist\YogoMFG\YogoMFG.exe (onedir). Inclut mod\, assets\ et tools\npi\.
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --windowed --name YogoMFG ^
  --icon assets\yogo.ico ^
  --add-data "mod;mod" ^
  --add-data "assets;assets" ^
  --add-data "tools\npi;tools\npi" ^
  --collect-all customtkinter ^
  yogomfg.py
echo.
echo Build fini: dist\YogoMFG\YogoMFG.exe
