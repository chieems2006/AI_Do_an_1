@echo off
rem Dung API va giao dien MSA (tim theo cong 8000/7860, dong luon cua so cmd cua CHAY_DU_AN.bat).
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
"%~dp0.venv\Scripts\python.exe" scripts\chay_du_an.py stop
timeout /t 3 >nul 2>&1
