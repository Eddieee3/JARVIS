# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# chromadb resuelve varios de sus submódulos (telemetry, backends de DB, etc.)
# de forma dinámica con importlib, así que el analizador estático de
# PyInstaller no los detecta solo. Se incluyen todos explícitamente.
hidden_chromadb = collect_submodules('chromadb')

a = Analysis(
    ['orb_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('orb_ui', 'orb_ui')],
    hiddenimports=hidden_chromadb + ['pystray._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JARVIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['orb_ui/icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JARVIS',
)
