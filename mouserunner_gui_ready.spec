# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


PROJECT_ROOT = Path(SPECPATH)


a = Analysis(
    [str(PROJECT_ROOT / 'mouserunner.py')],
    pathex=[str(PROJECT_ROOT), str(PROJECT_ROOT / 'mouse_runner')],
    binaries=[],
    datas=[(str(PROJECT_ROOT / 'mouserunner.ico'), '.')] + collect_data_files('tkinter'),
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='mouserunner_gui_ready',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(PROJECT_ROOT / 'mouserunner.ico')],
)
