# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from core.build_manifest import pyinstaller_hidden_imports


for required_path in ("main.py", "config", "帝王霸业图库"):
    candidate = PROJECT_ROOT / required_path
    if not candidate.exists():
        raise FileNotFoundError(f"缺少打包必需路径: {candidate}")

hidden_imports = [
    "tasks",
    "tasks.base",
    "tasks.reward",
    *pyinstaller_hidden_imports(PROJECT_ROOT),
]

a = Analysis(
    [str(PROJECT_ROOT / 'main.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'config'), 'config'),
        (str(PROJECT_ROOT / '帝王霸业图库'), '帝王霸业图库'),
    ],
    hiddenimports=hidden_imports,
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
    name='游戏助手',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='游戏助手',
)
