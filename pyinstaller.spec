# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import glew, sdl2

options = [("v", None, "OPTION")]

a = Analysis(  # noqa: F821
    ["src/main.py"],
    pathex=[],
    binaries=[("mesa/x64/opengl32.dll", ".")],  # default =[]
    datas=collect_data_files("network_puzzles"),  # noqa: F821
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
    exludes=["docutils", "unittest"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
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
