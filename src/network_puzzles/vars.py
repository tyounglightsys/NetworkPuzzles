import locale
import os
import sys
from copy import deepcopy
from pathlib import Path

from kivy.utils import platform

APP_TITLE = "NetworkPuzzles"
APP_MODULE = "network_puzzles"
os.environ["KIVY_DESKTOP_PATH_ID"] = APP_TITLE

# Set INSTALL type.
if hasattr(sys, "_MEIPASS"):
    INSTALL_TYPE = "pyinstaller"
# elif hasattr(sys, "getandroidapilevel"):
elif "ANDROID_ARGUMENT" in os.environ:
    INSTALL_TYPE = "apk"
elif "SNAP" in os.environ:
    INSTALL_TYPE = "snap"
else:
    INSTALL_TYPE = "python"

# Ref: https://kivy.org/doc/stable/api-kivy.utils.html#kivy.utils.platform
# 'win', 'linux', 'android', 'macosx', 'ios' or 'unknown'
OS = platform

# Set DATA DIR.
match INSTALL_TYPE:
    case "pyinstaller":
        DATA_DIR = Path(sys._MEIPASS) / APP_MODULE
    case _:  # "android", "python"
        DATA_DIR = Path(__file__).parent
if "NETWORKPUZZLES_DATA_DIR" in os.environ:
    DATA_DIR = Path(os.getenv("NETWORKPUZZLES_DATA_DIR"))

# Set USER DATA DIR.
# Try to match Kivy's own implementation; but the var is needed before App is
# initialized, so we determine it here explicitly.
# Ref: https://kivy.org/doc/stable/api-kivy.app.html#kivy.app.App.user_data_dir
match OS:
    case "win":
        USER_DATA_DIR = Path(os.getenv("APPDATA")) / APP_TITLE
    case "android":
        from android.storage import app_storage_path

        USER_DATA_DIR = Path(app_storage_path())
    case "linux":
        base_str = os.getenv("XDG_CONFIG_HOME")
        if base_str is None:
            base_dir = Path.home() / ".local" / "share"
        else:
            base_dir = Path(base_str)
        USER_DATA_DIR = base_dir / APP_TITLE
    case _:  # fallback
        USER_DATA_DIR = Path.home() / APP_TITLE
if not USER_DATA_DIR.is_dir():
    USER_DATA_DIR.mkdir()


class Session:
    # NOTE: Session is instantiated when the app opens, even before the UI is
    # known. And since the instantiated session is used in multiple modules, any
    # UI-specific updates to the instance still need to be applied, but that
    # happens in the `ui.py` module rather than here.
    def __init__(self):
        self.app = None
        self._device_type = None
        self._lang = None
        self.locale = str(locale.getlocale()[0])
        self.maclist: list = list()
        self.puzzlelist: list = list()
        self.puzzle = None
        self.packetstorm = False
        self.maxpackets = 0
        self.history = list()
        self.undolist = list()
        self.redolist = list()
        self.ui = None
        self.startinglevel = ""
        # WirelessReconnectDistance was 80, but that would not reach with Level5_WirelessRepeater.  90 was OK, but 100 made it 'easy'
        self.WirelessReconnectDistance = 120  # The equivalent of a constant.  Stored here to be accessed multiple places. 80: defined in EduNet. NB.cs line 373.
        self.WirelessFailureDistance = (
            self.WirelessReconnectDistance - 15
        )  # packets fail at this point

    @property
    def device_type(self) -> str:
        """Returns device type: 'desktop' or 'mobile'.

        Generally, the app will assume a touch interface on mobile devices and a
        mouse interface on desktop devices.
        """
        default = "mobile"

        if self._device_type is None:
            if "NETWORKPUZZLES_DEVICE_TYPE" in os.environ:
                # Dev override
                value = os.getenv("NETWORKPUZZLES_DEVICE_TYPE", "").lower()
                if value in ("desktop", "mobile"):
                    self._device_type = value
                else:
                    self._device_type = default
            elif OS in ("android", "ios"):
                self._device_type = "mobile"
            elif OS in ("linux", "macosx", "win"):
                self._device_type = "desktop"
            else:
                # Fallback
                self._device_type = default
        return self._device_type

    @property
    def lang(self):
        if self._lang is None:
            # Fallback to locale if saved data is bad.
            self._lang = self.locale[:2].upper()
            saved_lang_file = USER_DATA_DIR / "lang.txt"
            if saved_lang_file.is_file():
                lang = saved_lang_file.read_text()
                if len(lang) == 2:
                    self._lang = lang
        return self._lang

    def print(self, message):
        print("<default print method>")
        print(message)

    def store_undo(self, line: str, puzzle_json):
        """Store a deep copy of the puzzle state for use later"""
        if self.puzzle is not None:
            tostore = {"line": line, "puzzle_json": deepcopy(puzzle_json)}
            self.undolist.append(tostore)
