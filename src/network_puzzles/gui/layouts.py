import logging
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.metrics import sp
from kivy.properties import NumericProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from .. import session
from .base import NETWORK_ITEMS
from .buttons import MenuButton


class ThemedBoxLayout(BoxLayout):
    pass


class AppTray(ThemedBoxLayout):
    def __init__(
        self, anchor_pos=None, choices=list(), orientation="horizontal", **kwargs
    ):
        super().__init__(**kwargs)
        self.app = session.app
        self.anchor_pos = anchor_pos  # parent_button.pos as (x, y)
        self.choices = choices
        self.buttons = [MenuButton(c) for c in self.choices]
        self.orientation = orientation

    def close(self):
        self.clear_widgets()

    def open(self):
        for b in self.buttons:
            self.add_widget(b)
        self._set_size()
        self._set_pos()

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


class PuzzleLayout(RelativeLayout):
    terminal_font_size = NumericProperty(sp(12))
    terminal_line_height = NumericProperty(sp(12 + 4))
    terminal_lines = NumericProperty(7)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.items_menu_button = MenuButton(
            props={"text": "+", "cb": self.app.on_new_item, "info": "add new item"},
            pos_hint={"x": 0.005, "top": 0.99},
        )

        # Define button trays.
        self.items_tray = AppTray(
            anchor_pos=self.pos,
            choices=self._get_items_choices(),
            orientation="vertical",
        )
        self.infra_devices_tray = AppTray(
            anchor_pos=self.pos,
            choices=self._get_infra_devices_choices(),
        )
        self.user_devices_tray = AppTray(
            anchor_pos=self.pos,
            choices=self._get_user_devices_choices(),
        )

    def add_items_menu_button(self):
        self.add_widget(self.items_menu_button)

    def close_trays(self):
        # Close tray and subtrays if open.
        for tray in (
            self.infra_devices_tray,
            self.user_devices_tray,
            self.items_tray,
        ):
            if tray is not None:
                self._close_tray(tray)

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

    def _get_infra_devices_choices(self):
        choices = []
        for dtype, choice in NETWORK_ITEMS.get("devices").get("infrastructure").items():
            choice["cb"] = self.app.add_device
            choice["cb_kwargs"] = {"dtype": dtype}
            choice["orientation"] = "horizontal"
            choices.append(choice)
        return choices

    def _get_items_choices(self):
        return [
            {"img": "link.png", "cb": self.app.add_link, "info": "add link"},
            {
                "img": "Switch.png",
                "cb": self.app.on_new_infra_device,
                "info": "infrastructure devices",
            },
            {
                "img": "PC.png",
                "cb": self.app.on_new_user_device,
                "info": "user devices",
            },
        ]

    def _get_user_devices_choices(self):
        choices = []
        for dtype, choice in NETWORK_ITEMS.get("devices").get("user").items():
            choice["cb"] = self.app.add_device
            choice["cb_kwargs"] = {"dtype": dtype}
            choice["orientation"] = "horizontal"
            choices.append(choice)
        return choices

    def _close_tray(self, tray):
        tray.close()
        self.remove_widget(tray)

    def _open_tray(self, tray):
        self.add_widget(tray)
        tray.open()

    def _toggle_tray(self, tray, subtrays=None):
        # Open tray, if not open.
        if tray not in self.children:
            self._open_tray(tray)
        # Close tray and subtrays if not closed.
        else:
            # First make sure submenu trays aren't open.
            if subtrays:
                for subtray in subtrays:
                    if subtray is not None:
                        self._close_tray(subtray)
            self._close_tray(tray)
