class UI:
    TITLE = 'NetworkPuzzles'

    def console_write(self, line):
        """Used to show terminal output to the user."""
        raise NotImplementedError

    def load_puzzle(self, file_path):
        """Set up the UI based on the data in the puzzle file."""
        raise NotImplementedError

    def run(self):
        """Startup the app when first launched."""
        raise NotImplementedError


class CLI(UI):
    def run(self):
        print(self.TITLE)


class GUI(UI):
    def __init__(self, kivyapp):
        self.app = kivyapp()
        # self.app.title = self.TITLE  # inferred from App subclass in .gui

    def run(self):
        self.app.run()
