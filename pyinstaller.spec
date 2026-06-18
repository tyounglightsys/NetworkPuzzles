# -*- mode: python ; coding: utf-8 -*-

# from kivy.tools.packaging.pyinstaller_hooks import (
#     get_deps_all,
#     # get_deps_minimal,
#     hookspath,
#     runtime_hooks,
# )
from kivy_deps import glew, sdl2

a = Analysis(  # noqa: F821
    ["src/main.py"],
    pathex=[],
    # binaries=[("./mesa/x64/opengl32.dll", ".")],
    binaries=[*glew.dep_bins, *sdl2.dep_bins],
    datas=[],
    hiddenimports=[
        "kivy.core.window.window_sdl2",
        "kivy.core.audio.audio_sdl2",
        "kivy.core.image.img_sdl2",
        "kivy.core.text.text_sdl2",
        "kivy.core.clipboard.clipboard_sdl2",
    ],
    hookspath=[],
    # hookspath=hookspath(),
    hooksconfig={},
    runtime_hooks=[],
    # runtime_hooks=runtime_hooks(),
    excludes=[],
    noarchive=False,
    optimize=0,
    # **get_deps_all(),  # added
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    # *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],  # noqa: F821
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
