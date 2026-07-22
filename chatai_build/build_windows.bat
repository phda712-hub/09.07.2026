@echo off
REM ============================================================
REM  Gerador de .EXE - iPHDA ZENITH OMNI (chatai.py)
REM  Basta dar DUPLO-CLIQUE neste arquivo no Windows.
REM  Requisito: Python 3.10+ instalado e no PATH.
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo === [1/4] Verificando Python ===
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo === [2/4] Criando ambiente virtual (.venv) ===
if not exist ".venv" (
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"

echo.
echo === [3/4] Instalando dependencias (requests + pyinstaller) ===
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo === [4/4] Gerando o executavel (.exe) ===
pyinstaller --noconfirm --clean chatai.spec
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o .exe.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SUCESSO! O executavel foi gerado em:
echo     %~dp0dist\ChatAI_ZenithOmni.exe
echo ============================================================
echo.
echo Abrindo a pasta dist...
start "" "%~dp0dist"
pause
endlocal
