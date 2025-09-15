from kivy.metrics import dp
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app

    # def on_touch_up(self, touch):
    #     if self.collide_point(*touch.pos):
    #         if len(touch.grab_list) > 0:  # widget was touched instead of layout
    #             # return super().on_touch_up(touch)
    #             return True
    #         elif hasattr(self.app, "chosen_pos"):
    #             # Convert touch.pos to relative layout pos.
    #             self.app.chosen_pos = self.to_widget(*touch.pos)
    #             return True


class AppMenu(ThemedBoxLayout):
    def __init__(
        self, anchor_pos=None, choices=list(), orientation="horizontal", **kwargs
    ):
        super().__init__(**kwargs)
        self.app = session.app
        self.size_hint = (None, None)
        self.orientation = orientation
        if self.orientation == "horizontal":
            self.padding[1] = 0
            self.padding[3] = 0
        else:
            self.padding[0] = 0
            self.padding[2] = 0
        self.anchor_pos = anchor_pos  # parent_button.pos as (x, y)
        self.choices = choices

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
