@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   GERAR EXECUTAVEL - Manus API Pro
echo   - Arquivo unico (--onefile)
echo   - Sem console/janela preta (--noconsole)
echo   - Com icone (icone.ico)
echo ============================================================
echo.

set "PY_FILE=manus_api_gui_tkinter_full_profissional_checkpoint_chave_credito.py"
set "APP_NAME=ManusAPIPro"
set "ICON=icone.ico"

REM --- 1) Verifica o Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale o Python 3 em https://www.python.org/downloads/
    echo        e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

REM --- 2) Verifica os arquivos necessarios ---
if not exist "%PY_FILE%" (
    echo [ERRO] Arquivo nao encontrado: %PY_FILE%
    echo        Coloque este .bat na MESMA pasta do arquivo .py
    pause
    exit /b 1
)
if not exist "%ICON%" (
    echo [AVISO] icone.ico nao encontrado nesta pasta. O exe sera gerado SEM icone.
    set "ICON="
)

REM --- 3) Instala/atualiza dependencias e o PyInstaller ---
echo [1/2] Instalando dependencias (pode demorar na primeira vez)...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller requests pywebview PyMySQL Pillow PySocks
echo.

REM --- 4) Monta o comando e compila ---
echo [2/2] Compilando com PyInstaller...
if defined ICON (
    python -m PyInstaller --noconfirm --clean --onefile --noconsole --icon "%ICON%" --name "%APP_NAME%" --collect-all webview --hidden-import pymysql --hidden-import PIL --hidden-import socks "%PY_FILE%"
) else (
    python -m PyInstaller --noconfirm --clean --onefile --noconsole --name "%APP_NAME%" --collect-all webview --hidden-import pymysql --hidden-import PIL --hidden-import socks "%PY_FILE%"
)

echo.
if exist "dist\%APP_NAME%.exe" (
    echo ============================================================
    echo   OK! Executavel gerado em:  dist\%APP_NAME%.exe
    echo   Basta enviar/rodar esse unico arquivo .exe
    echo ============================================================
) else (
    echo [ERRO] Falha ao gerar o executavel. Leia as mensagens acima.
)
echo.
pause
