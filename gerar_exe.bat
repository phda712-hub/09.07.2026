@echo off
REM ============================================================
REM  Gera o executavel migrar_tudo.exe a partir de migrar_tudo.py
REM  Basta colocar este .bat na MESMA pasta do migrar_tudo.py
REM  e dar duplo clique (ou rodar no PowerShell/CMD).
REM ============================================================

echo.
echo [1/2] Instalando dependencias (pyinstaller, fdb, mysql-connector-python)...
python -m pip install --upgrade pyinstaller fdb mysql-connector-python
if errorlevel 1 (
    echo.
    echo ERRO ao instalar as dependencias. Verifique se o Python esta instalado
    echo e no PATH ^(comando: python --version^).
    pause
    exit /b 1
)

echo.
echo [2/2] Gerando o executavel...
pyinstaller --onefile --console --name migrar_tudo ^
    --collect-all mysql.connector ^
    --collect-submodules fdb ^
    migrar_tudo.py
if errorlevel 1 (
    echo.
    echo ERRO ao gerar o executavel.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  PRONTO! O executavel foi criado em:
echo      dist\migrar_tudo.exe
echo ============================================================
echo.
echo  OBS: a maquina onde o .exe rodar precisa ter o cliente do
echo  Firebird instalado (fbclient.dll) - normalmente ja existe
echo  onde o Firebird 2.5 esta instalado.
echo.
pause
