from kivy.app import App
from kivy.uix.button import Button


class ThemedButton(Button):
    pass


class ActionsButton(ThemedButton):  # can't use ActionButton b/c exists already
    def __init__(self, device, callback_data, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.callback_data = callback_data
        self.text = self.callback_data.get('text', '<text>')
        self.cb_func = self.callback_data.get('func')
        self.cb_kwargs = self.callback_data.get('kwargs', {})

    def callback(self):
        if callable(self.cb_func):
            self.cb_func(device=self.device, **self.cb_kwargs)


class Ping:
    def __init__(self, src, dest):
        self.app = App.get_running_app()
        self.app.root.ids.terminal.text = f"PING {dest}."