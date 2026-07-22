@echo off
REM ============================================================
REM  Gera o executavel (.exe) do chat_ia.py usando PyInstaller
REM  Basta dar duplo clique neste arquivo no Windows.
REM ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   GERADOR DE EXECUTAVEL - chat_ia.exe
echo ============================================================
echo.

REM --- 1) Verifica se o Python esta instalado ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no sistema.
    echo Instale o Python em https://www.python.org/downloads/
    echo e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python encontrado:
python --version
echo.

REM --- 2) Atualiza o pip e instala as dependencias ---
echo [2/4] Instalando dependencias (requests e pyinstaller)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install requests pyinstaller
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    echo Verifique sua conexao com a internet e tente novamente.
    echo.
    pause
    exit /b 1
)
echo.

REM --- 3) Gera o executavel ---
echo [3/4] Gerando o executavel (isso pode levar alguns minutos)...
python -m PyInstaller --onefile --console --name chat_ia --clean chat_ia.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel.
    echo.
    pause
    exit /b 1
)
echo.

REM --- 4) Finaliza ---
echo [4/4] Concluido!
echo.
if exist "dist\chat_ia.exe" (
    echo O executavel foi criado em:
    echo   %cd%\dist\chat_ia.exe
    echo.
    echo Abrindo a pasta com o executavel...
    start "" "%cd%\dist"
) else (
    echo [AVISO] Nao encontrei dist\chat_ia.exe. Verifique as mensagens acima.
)
echo.
echo Pressione qualquer tecla para sair.
pause >nul
endlocal
