class UI:
    TITLE = 'NetworkPuzzles'

    def run(self):
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
