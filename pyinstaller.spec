# -*- mode: python ; coding: utf-8 -*-

import logging
from pathlib import Path

from kivy_deps import glew, sdl2

# from PyInstaller.utils.hooks import collect_data_files

options = [("v", None, "OPTION")]
# kvs = [
#     (str(f), "./network_puzzles/gui/")
#     for f in Path("src/network_puzzles/gui").glob("*.kv")
# ]
# logging.debug(f"{kvs=}")

a = Analysis(  # noqa: F821
    ["src/main.py"],
    pathex=[],
    binaries=[("mesa/x64/opengl32.dll", ".")],  # default =[]
    # datas=collect_data_files("network_puzzles.gui"),  # default =[]  # doesn't collect anything
    datas=[],
    hiddenimports=[
        "kivy.core.window.window_sdl2",
        "kivy.core.audio.audio_sdl2",
        "kivy.core.image.img_sdl2",
        "kivy.core.text.text_sdl2",
        "kivy.core.clipboard.clipboard_sdl2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["docutils", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821

logging.debug(f"{a.datas=}")
exe = EXE(  # noqa: F821
    pyz,
    Tree("src/network_puzzles/gui/"),  # noqa: F821
    a.scripts,
    a.binaries,
    a.datas,
    # [],
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],  # noqa: F821
    name="NetworkPuzzles",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
