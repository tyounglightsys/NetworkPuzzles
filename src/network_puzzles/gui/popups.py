from kivy.uix.popup import Popup

from .. import session


class ThemedPopup(Popup):
    def __init__(self, **kwargs):
        # TODO: This popup automatically generates a GridLayout with 3 child
        # widgets: BoxLayout, Widget, Label. Better to set the content
        # explicitly when the popup is instantiated elsewhere.
        self.app = session.app
        super().__init__(**kwargs)


class ActionPopup(ThemedPopup):
    def on_cancel(self):
        self.dismiss()

    def on_okay(self):
        self.dismiss()


class CommandPopup(ActionPopup):
    def on_okay(self):
        self.app.ui.parse(self.ids.text_input.text)
        super().on_okay()
        # self.dismiss()


class ExceptionPopup(ThemedPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message

    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class PuzzleChooserPopup(ActionPopup):
    def on_load(self):
        self.app.selected_puzzle = self.ids.puzzles_view.selected_item.get("text")
        self.app.setup_puzzle()
        super().on_okay()


class PuzzleCompletePopup(ActionPopup):
    pass


#     def on_okay(self):
#         # TODO: Offer to proceed to the next puzzle.
#         self.dismiss()
