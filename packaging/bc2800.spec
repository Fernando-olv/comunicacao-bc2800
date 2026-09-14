# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis

spec_path = Path(SPECPATH).resolve()
spec_dir = spec_path.parent if spec_path.is_file() else spec_path
ROOT = spec_dir.parent
SRC = ROOT / "src"

a = Analysis(
    [str(SRC / "bc2800" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[],
    hiddenimports=["serial", "serial.tools.list_ports", "openpyxl", "PySide6"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BC2800 Receptor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="BC2800 Receptor",
)
