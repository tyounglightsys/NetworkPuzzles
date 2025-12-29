import locale
import os
import platform
import sys
from pathlib import Path


class Session:
    # NOTE: Session is instantiated when the app opens, even before the UI is
    # known. And since the instantiated session is used in multiple modules, any
    # UI-specific updates to the instance still need to be applied, but that
    # happens in the `ui.py` module rather than here.
    def __init__(self):
        self.app = None
        self.locale = str(locale.getlocale()[0])
        self.lang: str = self.locale[:2]
        self.maclist: list = list()
        self.puzzlelist: list = list()
        self.puzzle = None
        self.packetlist: list = list()
        self.packetstorm = False
        self.maxpackets = 0
        self.history = list()
        self.undolist = list()
        self.redolist = list()
        self.ui = None
        self.startinglevel = ""
        self.package_dir = Path(__file__).parent

    @property
    def device_type(self) -> str:
        """Returns device type: 'desktop' or 'mobile'.

        Generally, the app will assume a touch interface on mobile devices and a
        mouse interface on desktop devices.
        """
        if hasattr(sys, "getandroidapilevel"):
            # Android
            return "mobile"
        elif os.getenv("DISPLAY"):
            # Linux or Mac desktop
            return "desktop"
        elif os.getenv("COMPUTERNAME"):
            # Windows desktop
            return "desktop"
        elif platform.system() in ("iOS", "iPadOS"):
            # iPhone or IPad
            return "mobile"
        else:
            # Fallback
            return "mobile"

    def print(self, message):
        print("<default print method>")
        print(message)

    def add_undo_entry(self, forwards_cmd: str, backwards_cmd: str, payload=None):
        """Add a record to the undo list.
        The forwards command is used for redo,
        the backwards command is used for undo.
        the payload is used if we delete something and need to recover it."""
        newrec = {}
        newrec["forwards"] = forwards_cmd
        newrec["backwards"] = backwards_cmd
        newrec["payload"] = payload
        self.undolist.append(newrec)
