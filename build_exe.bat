@echo off
REM ============================================================
REM   LOJA QUANTUM - Gerador de Executavel (.exe)
REM   Modo: --onefile (arquivo unico) + --windowed (sem console)
REM   Icone: icone_loja.ico
REM ============================================================
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Build - LOJA QUANTUM

echo.
echo ============================================================
echo    GERADOR DE EXECUTAVEL - LOJA QUANTUM
echo ============================================================
echo.

REM ---------- 1) Verifica Python ----------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no PATH.
    echo        Instale o Python 3.10+ em https://www.python.org/downloads/
    echo        e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%v in ('python --version') do echo [OK] %%v encontrado.
echo.

REM ---------- 2) Atualiza pip e instala PyInstaller ----------
echo [1/4] Atualizando pip e instalando o PyInstaller...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERRO] Falha ao instalar o PyInstaller.
    pause
    exit /b 1
)
echo.

REM ---------- 3) Instala dependencias essenciais ----------
echo [2/4] Instalando dependencias essenciais do sistema...
set "ESSENCIAIS=ttkbootstrap pillow mysql-connector-python numpy openpyxl reportlab fpdf2 qrcode psutil bcrypt cryptography pycryptodome flask flask-cors flask-socketio pyttsx3 pyserial pywin32 comtypes SpeechRecognition"
for %%P in (%ESSENCIAIS%) do (
    echo    - instalando %%P ...
    python -m pip install --upgrade %%P >nul 2>&1
    if errorlevel 1 echo      [AVISO] Nao foi possivel instalar %%P (continuando^).
)
echo.

REM ---------- 3b) Dependencias opcionais (hardware / bluetooth) ----------
echo [3/4] Instalando dependencias opcionais (podem falhar sem problema^)...
for %%P in (pyusb bleak) do (
    echo    - opcional: %%P ...
    python -m pip install --upgrade %%P >nul 2>&1
)
echo.

REM ---------- 4) Gera o executavel ----------
echo [4/4] Gerando o executavel (isso pode demorar alguns minutos^)...
echo.
pyinstaller --noconfirm --clean --onefile --windowed ^
    --icon="icone_loja.ico" ^
    --name "LojaQuantum" ^
    --collect-all ttkbootstrap ^
    --collect-submodules mysql.connector ^
    --hidden-import win32timezone ^
    --hidden-import comtypes ^
    --hidden-import pyttsx3.drivers ^
    --hidden-import pyttsx3.drivers.sapi5 ^
    "Quantum_bkp.py"

if errorlevel 1 (
    echo.
    echo [ERRO] A geracao do executavel falhou. Verifique as mensagens acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    CONCLUIDO COM SUCESSO!
echo ============================================================
echo    O executavel esta em:  dist\LojaQuantum.exe
echo    (arquivo unico, sem console, com icone da loja^)
echo ============================================================
echo.
REM Abre a pasta com o resultado
if exist "dist\LojaQuantum.exe" start "" "dist"
pause
endlocal
