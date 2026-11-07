@echo off
rem Construit dist\YogoMFG.exe (onefile portable). NPI + mod\ + assets\ embarques dedans.
rem Donnees (config.json, .nip, covers) ecrites dans %LOCALAPPDATA%\YogoMFG, rien a cote du .exe.
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --onefile --windowed --uac-admin --name YogoMFG ^
  --icon assets\yogo.ico ^
  --add-data "mod;mod" ^
  --add-data "assets;assets" ^
  --add-data "tools\npi;tools\npi" ^
  --collect-all customtkinter ^
  yogomfg.py
if errorlevel 1 (
  echo.
  echo ECHEC du build. Si l'erreur est "Acces refuse" sur dist\YogoMFG.exe, ferme YogoMFG avant de relancer.
  exit /b 1
)
if not exist "dist\YogoMFG.exe" (
  echo.
  echo ECHEC du build: dist\YogoMFG.exe absent.
  exit /b 1
)
echo.
echo Build fini: dist\YogoMFG.exe
