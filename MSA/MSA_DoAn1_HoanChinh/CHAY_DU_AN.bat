@echo off
rem Chay du an MSA: API (cong 8000) + giao dien Gradio (cong 7860), moi phan mot cua so.
rem   CHAY_DU_AN.bat        Gemini that (doc GEMINI_API_KEY trong .env)
rem   CHAY_DU_AN.bat mock   Gemini gia lap - khong ton quota
rem Dung: dong 2 cua so "MSA API" va "MSA UI", hoac chay DUNG_DU_AN.bat
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title MSA - khoi dong

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [LỖI] Chưa có môi trường ảo .venv. Tạo bằng:
  echo     py -3.11 -m venv .venv
  echo     .venv\Scripts\python.exe -m pip install -r 05_Hoang\repo_skeleton\requirements.txt
  goto :fail
)

set "PYTHONUTF8=1"
if not defined HF_HUB_OFFLINE set "HF_HUB_OFFLINE=1"
if /i "%~1"=="mock" (
  set "MSA_LLM_MOCK=1"
  echo Chế độ Gemini GIẢ LẬP - không tốn quota.
) else (
  set "MSA_LLM_MOCK="
)

echo === Kiểm tra trước khi chạy ===
"%PY%" scripts\chay_du_an.py check
if errorlevel 1 goto :fail

echo === Mở API (cửa sổ "MSA API") ===
start "MSA API" cmd /k ""%PY%" scripts\chay_du_an.py api"
"%PY%" scripts\chay_du_an.py wait
if errorlevel 1 goto :fail

echo === Mở giao diện (cửa sổ "MSA UI") ===
start "MSA UI" cmd /k ""%PY%" scripts\chay_du_an.py ui"
"%PY%" scripts\chay_du_an.py wait-ui
if errorlevel 1 goto :fail

start "" "http://127.0.0.1:7860"
echo.
echo Đã chạy xong:
echo   Giao diện : http://127.0.0.1:7860
echo   API       : http://127.0.0.1:8000/docs  (Swagger)
echo Dừng: đóng 2 cửa sổ "MSA API" và "MSA UI", hoặc chạy DUNG_DU_AN.bat
echo.
if not "%MSA_NO_PAUSE%"=="1" pause
exit /b 0

:fail
echo.
echo Không chạy được - xem thông báo ở trên.
if not "%MSA_NO_PAUSE%"=="1" pause
exit /b 1
