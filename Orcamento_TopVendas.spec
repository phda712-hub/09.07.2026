# -*- mode: python ; coding: utf-8 -*-
# Arquivo de build do PyInstaller para gerar o Orcamento_TopVendas.exe
# Uso:  pyinstaller Orcamento_TopVendas.spec

block_cipher = None

a = Analysis(
    ['Orcamento_TopVendas.py'],
    pathex=[],
    binaries=[],
    # embute o icone dentro do .exe para ser encontrado em tempo de execucao
    datas=[
        ('icone_carrinho.ico', '.'),
        ('icone_carrinho.png', '.'),
    ],
    hiddenimports=['fdb', 'win32print', 'win32api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Orcamento_TopVendas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # sem janela de console (aplicacao grafica)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icone_carrinho.ico',   # icone do .exe
)
