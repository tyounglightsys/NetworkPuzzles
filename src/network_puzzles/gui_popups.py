from kivy.app import App
from kivy.uix.popup import Popup

from . import session
from .gui_buttons import ActionsButton


class AppPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()


class ActionsPopup(AppPopup):
    def __init__(self, device, actions, **kwargs):
        super().__init__(**kwargs)
        self.actions = actions
        self.device = device
    
    def on_open(self):
        # Add buttons.
        for callback_data in self.actions:
            b = ActionsButton(self.device, callback_data, text='test')
            self.children[0].add_widget(b)


class ExceptionPopup(AppPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message

    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class PuzzleChooserPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_dismiss(self):
        self.app.selected_puzzle = None

    def on_load(self):
        session.puzzle = self.app.ui.load_puzzle(self.app.selected_puzzle)
        self.app.setup_puzzle(session.puzzle)
        self.dismiss()