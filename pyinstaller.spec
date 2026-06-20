# -*- mode: python ; coding: utf-8 -*-

import logging
import sys
from pathlib import Path

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

# network_puzzles_tree = Tree(
#     "src\\network_puzzles",
#     excludes=["*.py"],
#     prefix="network_puzzles",
# )
# network_puzzles_datas = [(f[1], str(Path(f[0]).parent)) for f in network_puzzles_tree]

# logging.debug(f"{network_puzzles_datas=}")
# if len(network_puzzles_datas) == 0:
#     sys.exit(1)

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
    # datas=[*network_puzzles_datas],
    datas=[
        ("src\\network_puzzles\\gui\\*.kv", "network_puzzles\\gui"),
        ("src\\network_puzzles\\resources", "network_puzzles"),
    ],
    hookspath=hookspath(),  # default =[]
    hooksconfig={},
    runtime_hooks=runtime_hooks(),  # default =[]
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    # Tree(
    #     "src\\network_puzzles\\", prefix="network_puzzles"
    # ),  # explicitly grab full src code
    a.scripts,
    a.binaries,
    a.datas,
    # [],
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name="NetworkPuzzles",
    debug=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
)
