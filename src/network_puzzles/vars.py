import locale


class Session:
    # NOTE: Session is instantiated when the app opens, even before the UI is
    # known. And since the instantiated session is used in multiple modules, any
    # UI-specific updates to the instance still need to be applied, but that
    # happens in the `ui.py` module rather than here.
    def __init__(self):
        self.app = None
        self.locale = locale.getlocale()[0]
        self.lang: str = self.locale[:2]
        self.maclist: list = list()
        self.puzzlelist: list = list()
        self.puzzle = None
        self.packetlist: list = list()
        self.history = list()
    
    def print(self, message):
        print("<default print method>")
        print(message)
