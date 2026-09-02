@echo off
REM ============================================================================
REM  Gera reparar_vendas_duplicadas.exe a partir de reparar_vendas_duplicadas.py
REM  Quantum / Farma Quantum PDV
REM ============================================================================
REM  Basta dar 2 cliques neste .bat (ou rodar no CMD) na MESMA pasta onde
REM  esta o arquivo reparar_vendas_duplicadas.py.
REM  Requisitos: Python 3 instalado e no PATH (marque "Add Python to PATH"
REM  na instalacao). O restante (PyInstaller / mysql-connector) e instalado
REM  automaticamente por este script.
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "SCRIPT=reparar_vendas_duplicadas.py"
set "NOME=reparar_vendas_duplicadas"

echo ============================================================
echo   GERADOR DE EXE - %SCRIPT%
echo ============================================================
echo.

REM ---- 1) Localiza o Python (py launcher ou python) -------------------------
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [X] Python nao encontrado no PATH.
    echo     Instale em https://www.python.org/downloads/ e marque
    echo     "Add Python to PATH". Depois rode este .bat novamente.
    echo.
    pause
    exit /b 1
)
echo [i] Usando interpretador: %PY%
%PY% --version
echo.

REM ---- 2) Verifica se o .py existe ------------------------------------------
if not exist "%SCRIPT%" (
    echo [X] Nao encontrei "%SCRIPT%" nesta pasta:
    echo     %CD%
    echo     Coloque este .bat na MESMA pasta do arquivo .py.
    echo.
    pause
    exit /b 1
)

REM ---- 3) Instala/atualiza as dependencias ----------------------------------
echo [i] Instalando/atualizando pip, PyInstaller e conector MySQL...
%PY% -m pip install --upgrade pip                          >nul 2>&1
%PY% -m pip install --upgrade pyinstaller                  || goto :ERRO_DEP
%PY% -m pip install --upgrade mysql-connector-python       || goto :ERRO_DEP
REM PyMySQL como conector alternativo (opcional, nao aborta se falhar)
%PY% -m pip install --upgrade pymysql                      >nul 2>&1
echo [i] Dependencias OK.
echo.

REM ---- 4) Limpa builds anteriores -------------------------------------------
if exist "build"        rmdir /s /q "build"
if exist "__pycache__"  rmdir /s /q "__pycache__"
if exist "%NOME%.spec"  del /q "%NOME%.spec"

REM ---- 5) Gera o executavel --------------------------------------------------
echo [i] Compilando... (pode levar 1 a 3 minutos)
echo.
%PY% -m PyInstaller ^
    --onefile ^
    --console ^
    --name "%NOME%" ^
    --collect-submodules mysql.connector ^
    --hidden-import mysql.connector ^
    --hidden-import mysql.connector.locales.eng.client_error ^
    --hidden-import mysql.connector.plugins.mysql_native_password ^
    --hidden-import mysql.connector.plugins.caching_sha2_password ^
    --hidden-import mysql.connector.plugins.sha256_password ^
    --hidden-import mysql.connector.plugins.mysql_clear_password ^
    --hidden-import pymysql ^
    "%SCRIPT%"

if errorlevel 1 goto :ERRO_BUILD

REM ---- 6) Resultado ----------------------------------------------------------
echo.
if exist "dist\%NOME%.exe" (
    echo ============================================================
    echo   [OK] EXE gerado com sucesso!
    echo   Arquivo: %CD%\dist\%NOME%.exe
    echo ============================================================
    echo.
    echo   Como usar (no CMD, dentro da pasta dist):
    echo       %NOME%.exe --dry-run
    echo       %NOME%.exe --add-unique-index
    echo.
) else (
    echo [X] Compilou mas nao encontrei dist\%NOME%.exe. Verifique o log acima.
)
pause
exit /b 0

:ERRO_DEP
echo.
echo [X] Falha ao instalar dependencias. Verifique sua conexao com a internet
echo     e se o Python/pip estao funcionando (%PY% -m pip --version).
echo.
pause
exit /b 1

:ERRO_BUILD
echo.
echo [X] Falha ao gerar o executavel. Veja as mensagens acima.
echo.
pause
exit /b 1
