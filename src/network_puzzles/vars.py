import locale
import os
import platform
import sys
from copy import deepcopy
from pathlib import Path

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

# Set OS type.
if "DYLD_LIBRARY_PATH" in os.environ:
    OS = "mac"
elif "DISPLAY" in os.environ:
    OS = "linux"
elif "COMPUTERNAME" in os.environ:
    OS = "windows"
elif "ANDROID_ROOT" in os.environ:
    OS = "android"
else:
    OS = "unknown"

# Set DATA DIR.
match INSTALL_TYPE:
    case "pyinstaller":
        DATA_DIR = Path(sys._MEIPASS) / "network_puzzles"
    case _:  # "android", "python"
        DATA_DIR = Path(__file__).parent
if "NETWORKPUZZLES_DATA_DIR" in os.environ:
    DATA_DIR = Path(os.getenv("NETWORKPUZZLES_DATA_DIR"))


class Session:
    # NOTE: Session is instantiated when the app opens, even before the UI is
    # known. And since the instantiated session is used in multiple modules, any
    # UI-specific updates to the instance still need to be applied, but that
    # happens in the `ui.py` module rather than here.
    def __init__(self):
        self.app = None
        self._device_type = None
        self.locale = str(locale.getlocale()[0])
        self.lang: str = self.locale[:2]
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
            elif OS == "android":
                self._device_type = "mobile"
            elif OS in ("linux", "mac", "windows"):
                self._device_type = "desktop"
            elif platform.system() in ("iOS", "iPadOS"):
                # iPhone or IPad
                self._device_type = "mobile"
            else:
                # Fallback
                self._device_type = default
        return self._device_type

    def print(self, message):
        print("<default print method>")
        print(message)

    def store_undo(self, line: str, puzzle_json):
        """Store a deep copy of the puzzle state for use later"""
        if self.puzzle is not None:
            tostore = {"line": line, "puzzle_json": deepcopy(puzzle_json)}
            self.undolist.append(tostore)
