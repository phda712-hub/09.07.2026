@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Quantum Farma - Gerador de Executavel (.exe)

REM ================================================================
REM  Converte Quantum_Farma_do_cesar.py em Quantum_Farma.exe
REM  usando PyInstaller.
REM
REM  COMO USAR:
REM   1) Coloque este .bat na MESMA pasta do arquivo .py
REM   2) De um duplo clique neste arquivo
REM   3) Aguarde. O .exe sera criado na subpasta "dist"
REM ================================================================

REM ---- Configuracoes (pode ajustar) ----
set "PYFILE=Quantum_Farma_do_cesar.py"
set "APPNAME=Quantum_Farma"
set "ICON=ico.ico"
REM CONSOLE=0 -> aplicativo grafico sem janela preta
REM CONSOLE=1 -> mostra o console (util para ver erros/depurar)
set "CONSOLE=1"

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
echo [1/3] Atualizando o pip...
%PY% -m pip install --upgrade pip
echo.

REM ---- 4) Instala as dependencias ----
echo [2/3] Instalando dependencias (pode demorar alguns minutos)...
%PY% -m pip install --upgrade pyinstaller mysql-connector-python Pillow ttkbootstrap reportlab qrcode pyserial pywin32 numpy openpyxl bcrypt cryptography flask psutil requests
if errorlevel 1 (
    echo.
    echo [AVISO] Alguma dependencia pode ter falhado ao instalar.
    echo         O processo vai continuar mesmo assim.
)
echo.

REM ---- 5) Define modo janela/console ----
set "MODE_ARG=--windowed"
if "%CONSOLE%"=="1" set "MODE_ARG=--console"

REM ---- 6) Define o icone (se existir) ----
set "ICON_ARG="
if exist "%ICON%" (
    set "ICON_ARG=--icon %ICON% --add-data %ICON%;."
    echo [OK] Icone encontrado: %ICON%
) else (
    echo [INFO] Icone "%ICON%" nao encontrado. O EXE sera gerado sem icone personalizado.
)
echo.

REM ---- 7) Gera o executavel ----
echo [3/3] Gerando o executavel... isso pode demorar bastante. Aguarde!
echo.
%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  %MODE_ARG% ^
  --name "%APPNAME%" ^
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

echo.
if exist "dist\%APPNAME%.exe" (
    echo ================================================================
    echo   [SUCESSO] Executavel gerado em:
    echo   %CD%\dist\%APPNAME%.exe
    echo ================================================================
    echo.
    echo   Dica: se o programa usa o icone "%ICON%" ou outros arquivos
    echo   de dados, mantenha-os na mesma pasta do .exe quando abrir.
) else (
    echo ================================================================
    echo   [FALHOU] O .exe nao foi gerado.
    echo   Leia as mensagens acima para identificar o erro.
    echo   Dica: mude "set CONSOLE=0" para "set CONSOLE=1" no topo
    echo   deste .bat e rode de novo para ver os erros em detalhe.
    echo ================================================================
)
echo.
pause
endlocal
