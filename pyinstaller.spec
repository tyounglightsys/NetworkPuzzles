# -*- mode: python ; coding: utf-8 -*-

# Ref: https://kivy.org/doc/stable/guide/packaging-windows.html
from kivy_deps import glew, gstreamer, sdl2

a = Analysis(  # noqa: F821
    ["src/main.py"],
    pathex=[],
    # binaries=[("./mesa/x64/opengl32.dll", ".")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],  # noqa: F821
    name="NetworkPuzzles",
    debug=False,
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
