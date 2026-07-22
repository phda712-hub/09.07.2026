# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para iPHDA ZENITH OMNI (chatai.py)
# Uso: pyinstaller chatai.spec

block_cipher = None

a = Analysis(
    ['../chatai.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'requests',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.simpledialog',
        'tkinter.messagebox',
        'sqlite3',
        'ftplib',
    ],
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
    name='ChatAI_ZenithOmni',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # False = sem janela de terminal (app GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',      # descomente e coloque um icon.ico nesta pasta se quiser icone
)
