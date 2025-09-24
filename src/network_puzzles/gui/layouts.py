import logging
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.metrics import sp
from kivy.properties import NumericProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.relativelayout import RelativeLayout

from .. import session
from .buttons import MenuButton


class ThemedBoxLayout(BoxLayout):
    pass


class PuzzleLayout(RelativeLayout):
    terminal_font_size = NumericProperty(sp(12))
    terminal_line_height = NumericProperty(sp(12 + 4))
    terminal_lines = NumericProperty(7)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app

    def get_height(self):
        # Window height minus terminal area height.
        h = (
            Window.height
            - self.parent.padding[1]
            - self.parent.padding[3]
            - (
                self.terminal_lines * self.terminal_line_height
            )  # expicitly calculated to equal terminal height
            - self.parent.spacing
        )
        logging.debug(f"GUI: PuzzleLayout height: {h}")
        return h

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if touch.button == "left" or touch.button is None:
                if hasattr(self.app, "chosen_pos"):
                    # NOTE: If touch.grab_list is populated it means that a
                    # widget was touched instead of empty space. Do not set the
                    # chosen_pos, wait instead for another touch. Either way, True
                    # should be returned so that the touch is not propagated.
                    if len(touch.grab_list) == 0:
                        self.app.chosen_pos = self.to_widget(*touch.pos)
                    return True
                else:
                    # NOTE: The touch has to be explicitly passed on so that other
                    # child widgets (e.g. Links) are notified.
                    return super().on_touch_up(touch)


class AppMenu(ThemedBoxLayout):
    def __init__(
        self, anchor_pos=None, choices=list(), orientation="horizontal", **kwargs
    ):
        super().__init__(**kwargs)
        self.app = session.app
        self.anchor_pos = anchor_pos  # parent_button.pos as (x, y)
        self.choices = choices
        self.orientation = orientation

    def open(self):
        for c in self.choices:
            self.add_widget(MenuButton(c))
        self._set_size()
        self._set_pos()

    def close(self):
        self.clear_widgets()

    def _set_pos(self):
        if self.orientation == "horizontal":
            # NOTE: The tray's pos is immediately adjacent to the anchor button.
            x = self.anchor_pos[0] + self.height
            y = self.anchor_pos[1]
        else:
            # NOTE: The tray's pos is offset down from the anchor button by the
            # tray's height.
            x = self.anchor_pos[0]
            y = self.anchor_pos[1] - self.height
        self.pos = (x, y)

    def _set_size(self):
        length = len(self.children)
        breadth = self.app.BUTTON_MAX_H + dp(10)  # 10px more for padding
        if self.orientation == "horizontal":
            self.width = length * breadth
            self.height = breadth
        else:
            self.width = breadth
            self.height = length * breadth


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """Adds selection and focus behaviour to the view."""

    pass
