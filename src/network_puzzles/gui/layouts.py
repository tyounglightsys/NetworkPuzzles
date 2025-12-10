import logging

from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.relativelayout import RelativeLayout

from .. import _, session
from .base import NETWORK_ITEMS
from .buttons import MenuButton


class ThemedBoxLayout(BoxLayout):
    pass


class SingleRowLayout(ThemedBoxLayout):
    pass


class ActionPopupButtons(SingleRowLayout):
    cancel_text = StringProperty(f"{_('Cancel')}")
    okay_text = StringProperty(f"{_('Okay')}")

    # Register custom events to be passed onto root popup, etc.
    # ref: https://stackoverflow.com/questions/65551226/kivy-reusing-a-toggle-button-layout-but-assigning-different-functions-to-the-b/66181173#66181173
    def __init__(self, **kwargs):
        self.register_event_type("on_cancel")
        self.register_event_type("on_okay")
        super().__init__(**kwargs)

    def cancel(self):
        # self.on_cancel()
        self.dispatch("on_cancel")

    def okay(self):
        # self.on_okay()
        self.dispatch("on_okay")

    def on_cancel(self):
        pass

    def on_okay(self):
        pass


class AppTray(ThemedBoxLayout):
    def __init__(
        self, choices=list(), orientation="horizontal", parent_button=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.app = session.app
        self.parent_button = parent_button
        self.choices = choices
        self.buttons = [MenuButton(c) for c in self.choices]
        self.orientation = orientation

    @property
    def is_open(self):
        return len(self.children) > 0

    def close(self):
        self.clear_widgets()
        self.app.root.ids.layout.remove_widget(self)

    def open(self):
        self.app.root.ids.layout.add_widget(self)
        for b in self.buttons:
            self.add_widget(b)
        self._set_size()
        self._set_pos()

    def _set_pos(self):
        if self.orientation == "horizontal":
            # NOTE: The tray's pos is immediately adjacent to the anchor button.
            x = self.parent_button.pos[0] + self.height
            y = self.parent_button.pos[1]
        else:
            # NOTE: The tray's pos is offset down from the anchor button by the
            # tray's height.
            x = self.parent_button.pos[0]
            y = self.parent_button.pos[1] - self.height
        self.pos = (x, y)

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

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
            parent_button=self.items_menu_button,
            choices=self._get_items_choices(),
            orientation="vertical",
        )
        self.infra_devices_tray = AppTray(
            parent_button=self.items_tray.buttons[1],
            choices=self._get_infra_devices_choices(),
        )
        self.user_devices_tray = AppTray(
            parent_button=self.items_tray.buttons[2],
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
            tray.close()

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
