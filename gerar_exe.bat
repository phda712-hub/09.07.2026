@echo off
REM ============================================================================
REM  Gera o Orcamento_TopVendas.exe (Windows) com o icone do carrinho azul.
REM  Basta dar DOIS CLIQUES neste arquivo no Windows (com Python instalado).
REM ============================================================================
chcp 65001 >nul
title Gerando Orcamento_TopVendas.exe
cd /d "%~dp0"

echo.
echo ==========================================================
echo   INSTALANDO DEPENDENCIAS (pip)
echo ==========================================================
python -m pip install --upgrade pip
python -m pip install pyinstaller fdb pywin32 pillow

echo.
echo ==========================================================
echo   (RE)GERANDO O ICONE DO CARRINHO
echo ==========================================================
if not exist "icone_carrinho.ico" (
    python gerar_icone.py
)

echo.
echo ==========================================================
echo   COMPILANDO O EXECUTAVEL
echo ==========================================================
python -m PyInstaller --noconfirm --clean Orcamento_TopVendas.spec

echo.
echo ==========================================================
echo   PRONTO!
echo ==========================================================
echo O executavel foi gerado em:  dist\Orcamento_TopVendas.exe
echo.
pause
