from kivy.uix.button import Button


class ThemedButton(Button):
    pass


class CommandButton(ThemedButton):
    def __init__(self, callback, command, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.command = command
        # TODO: Parse text from passed command?
        self.text = command
    
    def on_press(self):
        self.callback(self.command)
