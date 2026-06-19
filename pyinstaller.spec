# -*- mode: python ; coding: utf-8 -*-

from kivy.tools.packaging.pyinstaller_hooks import (
    # get_deps_all,
    get_deps_minimal,
    hookspath,
    runtime_hooks,
)
from kivy_deps import glew, sdl2

# from PyInstaller.utils.hooks import collect_data_files

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
    ["src\\main.py"],
    pathex=[],
    binaries=[*minimal_deps.get("binaries", []), ("mesa\\x64\\opengl32.dll", ".")],
    hiddenimports=[
        *minimal_deps.get("hiddenimports", []),
        "kivy.core.window.window_sdl2",  # somehow gets missed
        "kivy.core.clipboard.clipboard_sdl2",  # somehow gets missed
    ],
    excludes=[*minimal_deps.get("excludes", []), "docutils", "unittest"],
    # datas=collect_data_files("network_puzzles"),  # finds nothing
    datas=[],
    hookspath=hookspath(),  # default =[]
    hooksconfig={},
    runtime_hooks=runtime_hooks(),  # default =[]
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    Tree(
        "src\\network_puzzles\\", prefix="network_puzzles"
    ),  # explicitly grab full src code
    a.scripts,
    a.binaries,
    a.datas,
    # [],
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name="NetworkPuzzles",
    debug=True,
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
)
