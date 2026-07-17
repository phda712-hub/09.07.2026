@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Quantum Farma - Gerador de Executavel (.exe)

REM ================================================================
REM  Converte Quantum_Farma_do_cesar.py em executavel (.exe)
REM  usando PyInstaller. Gera DOIS executaveis:
REM    - Quantum_Farma.exe        -> SEM console (uso normal)
REM    - Quantum_Farma_debug.exe  -> COM console (para depurar erros)
REM
REM  COMO USAR:
REM   1) Coloque este .bat na MESMA pasta do arquivo .py (e do ico.ico)
REM   2) De um duplo clique neste arquivo
REM   3) Aguarde. Os .exe serao criados na subpasta "dist"
REM ================================================================

REM ---- Configuracoes (pode ajustar) ----
set "PYFILE=Quantum_Farma_do_cesar.py"
set "APPNAME=Quantum_Farma"
set "ICON=ico.ico"

cd /d "%~dp0"

echo ================================================================
echo   GERADOR DE EXECUTAVEL - %APPNAME%
echo ================================================================
echo.

REM ---- 1) Localiza o Python ----
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale o Python 3.10 ou superior em:
    echo        https://www.python.org/downloads/
    echo        e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)
echo [OK] Python encontrado:
%PY% --version
echo.

REM ---- 2) Verifica o arquivo .py ----
if not exist "%PYFILE%" (
    echo [ERRO] Nao encontrei "%PYFILE%" nesta pasta:
    echo        %CD%
    echo        Coloque este .bat na mesma pasta do arquivo Python.
    echo.
    pause
    exit /b 1
)

REM ---- 3) Atualiza o pip ----
echo [1/4] Atualizando o pip...
%PY% -m pip install --upgrade pip
echo.

REM ---- 4) Instala as dependencias ----
echo [2/4] Instalando dependencias (pode demorar alguns minutos)...
%PY% -m pip install --upgrade pyinstaller mysql-connector-python Pillow ttkbootstrap reportlab qrcode pyserial pywin32 numpy openpyxl bcrypt cryptography flask psutil requests
if errorlevel 1 (
    echo.
    echo [AVISO] Alguma dependencia pode ter falhado ao instalar.
    echo         O processo vai continuar mesmo assim.
)
echo.

REM ---- 5) Define o icone (se existir) ----
set "ICON_ARG="
if exist "%ICON%" (
    set "ICON_ARG=--icon %ICON% --add-data %ICON%;."
    echo [OK] Icone encontrado: %ICON%
) else (
    echo [INFO] Icone "%ICON%" nao encontrado. Os EXE serao gerados sem icone personalizado.
)
echo.

REM ---- 6) Gera os DOIS executaveis ----
echo [3/4] Gerando "%APPNAME%.exe" (SEM console - uso normal)...
echo.
call :build "%APPNAME%" "--windowed" "build_normal"

echo.
echo [4/4] Gerando "%APPNAME%_debug.exe" (COM console - para depurar)...
echo.
call :build "%APPNAME%_debug" "--console" "build_debug"

REM ---- 7) Resultado ----
echo.
echo ================================================================
echo   RESULTADO
echo ================================================================
if exist "dist\%APPNAME%.exe" (
    echo   [OK] SEM console : %CD%\dist\%APPNAME%.exe
) else (
    echo   [FALHOU] %APPNAME%.exe nao foi gerado.
)
if exist "dist\%APPNAME%_debug.exe" (
    echo   [OK] COM console : %CD%\dist\%APPNAME%_debug.exe
) else (
    echo   [FALHOU] %APPNAME%_debug.exe nao foi gerado.
)
echo ================================================================
echo.
echo   Use o "%APPNAME%.exe" no dia a dia (sem a tela preta).
echo   Se ele fechar sozinho / der erro, rode o "%APPNAME%_debug.exe"
echo   para ver a mensagem de erro no console.
echo.
echo   Dica: mantenha o "%ICON%" e os arquivos de dados na mesma
echo   pasta do .exe quando for abrir.
echo.
pause
endlocal
goto :fim

REM ================================================================
REM  Subrotina de build
REM   %~1 = nome do exe   %~2 = modo (--windowed/--console)   %~3 = workpath
REM ================================================================
:build
set "B_NAME=%~1"
set "B_MODE=%~2"
set "B_WORK=%~3"
%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  %B_MODE% ^
  --name "%B_NAME%" ^
  --workpath "%B_WORK%" ^
  --specpath "%B_WORK%" ^
  %ICON_ARG% ^
  --collect-all ttkbootstrap ^
  --collect-all reportlab ^
  --collect-submodules mysql.connector ^
  --hidden-import mysql.connector.plugins.mysql_native_password ^
  --hidden-import mysql.connector.plugins.caching_sha2_password ^
  --hidden-import mysql.connector.plugins.sha256_password ^
  --hidden-import mysql.connector.plugins.mysql_clear_password ^
  --hidden-import mysql.connector.locales.eng.client_error ^
  --hidden-import PIL._tkinter_finder ^
  --hidden-import win32timezone ^
  --hidden-import qrcode ^
  --hidden-import openpyxl ^
  "%PYFILE%"
goto :eof

:fim
