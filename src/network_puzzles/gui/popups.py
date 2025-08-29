from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.uix.popup import Popup

from .. import session


class AppPopup(Popup):
    def __init__(self, **kwargs):
        # TODO: This popup automatically generates a GridLayout with 3 child
        # widgets: BoxLayout, Widget, Label. Better to set the content
        # explicitly when the popup is instantiated elsewhere.
        self.app = session.app
        super().__init__(**kwargs)

    def _update_sep_color(self):
        # Set separator color according to theme.
        w = self.children[0].children[1]
        with w.canvas:
            Color(rgba=self.app.theme.detail)
            Rectangle(pos=w.pos, size=w.size)

    def on_open(self):
        self._update_sep_color()


class CommandPopup(AppPopup):
    def on_okay(self):
        self.app.ui.parse(self.ids.text_input.text)
        self.dismiss()


class ExceptionPopup(AppPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message

    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class PuzzleCompletePopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_okay(self):
        # TODO: Offer to proceed to the next puzzle.
        self.dismiss()
