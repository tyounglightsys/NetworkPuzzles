# -*- mode: python ; coding: utf-8 -*-

from kivy.tools.packaging.pyinstaller_hooks import (
    # get_deps_all,
    get_deps_minimal,
    hookspath,
    runtime_hooks,
)
from kivy_deps import glew, sdl2

# returns dict with keys 'binaries', 'hiddenimports', and 'excludes'
# Ref: https://github.com/kivy/kivy/blob/master/kivy/tools/packaging/pyinstaller_hooks/__init__.py
minimal_deps = get_deps_minimal(
    audio=None,
    camera=None,
    clipboard=True,
    image=True,
    spelling=True,
    text=True,
    video=None,
    window=True,
)

a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("src\\network_puzzles\\gui\\*.kv", "network_puzzles\\gui"),
        ("src\\network_puzzles\\resources", "network_puzzles\\resources"),
    ],
    hiddenimports=[
        *minimal_deps.get("hiddenimports", []),
        "kivy.core.window.window_sdl2",  # somehow gets missed
        "kivy.core.clipboard.clipboard_sdl2",  # somehow gets missed
    ],
    hookspath=hookspath(),  # default =[]
    hooksconfig={},
    runtime_hooks=runtime_hooks(),  # default =[]
    excludes=[*minimal_deps.get("excludes", []), "docutils", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NetworkPuzzlesd",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name="NetworkPuzzlesd",
)
