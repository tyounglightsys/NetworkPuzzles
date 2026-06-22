# -*- mode: python ; coding: utf-8 -*-

import sys

from kivy.tools.packaging.pyinstaller_hooks import (
    # get_deps_all,
    get_deps_minimal,
    hookspath,
    runtime_hooks,
)

# if sys.platform == "win32":
from kivy_deps import glew, sdl2

#     missed_imports = []
# else:
#     missed_imports = ["kivy.core.window.window_x11"]

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
    binaries=[*minimal_deps.get("binaries", [])],
    datas=[
        ("src/network_puzzles/gui/*.kv", "network_puzzles/gui"),
        ("src/network_puzzles/resources", "network_puzzles/resources"),
    ],
    hiddenimports=[
        *minimal_deps.get("hiddenimports", []),
        "kivy.core.window.window_sdl2",
        "kivy.core.clipboard.clipboard_sdl2",  # somehow gets missed
    ],
    excludes=[*minimal_deps.get("excludes", []), "docutils", "unittest"],
    hookspath=hookspath(),  # default =[]
    hooksconfig={},
    runtime_hooks=runtime_hooks(),  # default =[]
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

name = "NetworkPuzzles"
debug = True
strip = False
console = True
disable_windowed_traceback = False
target_arch = None
if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        # [],
        *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
        name=name,
        debug=debug,
        strip=strip,
        upx=True,
        upx_exclude=[],
        console=console,
        disable_windowed_traceback=disable_windowed_traceback,
        target_arch=target_arch,
    )
else:  # linux OS
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
        name=name,
        debug=debug,
        strip=strip,
        upx=False,
        console=console,
        disable_windowed_traceback=disable_windowed_traceback,
        target_arch=target_arch,
    )
