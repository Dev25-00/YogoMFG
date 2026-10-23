@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul && (start "" pythonw yogomfg.py) || python yogomfg.py
