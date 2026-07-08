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
    ["src\\main.py"],
    pathex=[],
    binaries=[*minimal_deps.get("binaries", [])],
    datas=[
        ("src\\network_puzzles\\gui\\*.kv", "network_puzzles\\gui"),
        ("src\\network_puzzles\\resources", "network_puzzles\\resources"),
    ],
    hiddenimports=[
        *minimal_deps.get("hiddenimports", []),
        "kivy.core.window.window_sdl2",  # somehow gets missed
        "kivy.core.clipboard.clipboard_sdl2",  # somehow gets missed
    ],
    excludes=[*minimal_deps.get("excludes", []), "docutils", "unittest"],
    hookspath=hookspath(),  # default =[]
    hooksconfig={},
    runtime_hooks=runtime_hooks(),  # default =[]
    noarchive=False,
    optimize=0,
)

splash = Splash(
    "src/network_puzzles/resources/images/NBIcoLG.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(10, 50),
    text_size=12,
    text_color='black',
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    splash.datas,
    # a.binaries,
    # a.datas,
    # [],
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name="NetworkPuzzles",
    icon="src/network_puzzles/resources/images/NBIco.ico",
    debug=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
)
