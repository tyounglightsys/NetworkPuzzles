# import logging
import traceback
from dataclasses import dataclass
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.properties import StringProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.recycleview import RecycleView
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from typing import Tuple

from .. import session
from .popups import ExceptionPopup


LOCATION_MAX_X = 900
LOCATION_MAX_Y = 850
NETWORK_ITEMS = {
    "links": {
        "link": {"img": "link.png"},
    },
    "devices": {
        "user": {
            "cellphone": {"img": "cellphone.png"},
            "copier": {"img": "Copier.png"},
            "ip_phone": {"img": "ip_phone.png"},
            "laptop": {"img": "Laptop.png"},
            "microwave": {"img": "microwave.png"},
            "pc": {"img": "PC.png"},
            "printer": {"img": "Printer.png"},
            "tablet": {"img": "tablet.png"},
        },
        "infrastructure": {
            "firewall": {"img": "firewall.png"},
            "fluorescent": {"img": "fluorescent.png"},
            "net_hub": {"img": "Hub.png"},
            "net_switch": {"img": "Switch.png"},
            "router": {"img": "Router.png"},
            "server": {"img": "Server.png"},
            "tree": {"img": "tree.png"},
            "wap": {"img": "WAP.png"},
            "wbridge": {"img": "WBridge.png"},
            "wrepeater": {"img": "WRepeater.png"},
            "wrouter": {"img": "WRouter.png"},
        },
    },
}


class AppExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        ExceptionPopup(message=traceback.format_exc()).open()
        # return ExceptionManager.RAISE  # kills app right away
        return ExceptionManager.PASS


class AppRecView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.selected_item = None

    def on_selection(self, idx):
        self.selected_item = self.data[idx]


class ThemedCheckBox(CheckBox):
    name = StringProperty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app

    def get_popup(self):
        for win in self.get_parent_window().children:
            # Only Popup widget has 'content' attribute.
            if hasattr(win, "content"):
                return win

    def on_activate(self):
        self.app.on_checkbox_activate(self)


class Packet(Widget):
    pass


class HelpHighlight(Widget):
    def __init__(self, name=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name


class HelpSlider(Slider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.value = HelpLevel.FULL
        self.bind(value=self.app.update_help)


@dataclass
class HelpLevel:
    NONE = 0
    BASIC = 1
    HINTS = 2
    FULL = 3


@dataclass
class Theme:
    name: str
    fg3: Tuple[float, float, float, float]
    fg2: Tuple[float, float, float, float]
    fg1: Tuple[float, float, float, float]
    neutral: Tuple[float, float, float, float]
    detail: Tuple[float, float, float, float]
    bg1: Tuple[float, float, float, float]
    bg2: Tuple[float, float, float, float]
    bg3: Tuple[float, float, float, float]


@dataclass
class LightGrayscaleTheme(Theme):
    name = "Grayscale, light"
    fg3 = (0.10, 0.10, 0.10, 1)
    fg2 = (0.15, 0.15, 0.15, 1)
    fg1 = (0.20, 0.20, 0.20, 1)
    neutral = (0.5, 0.5, 0.5, 1)
    detail = (0.80, 0.80, 0.80, 1)
    bg1 = (0.80, 0.80, 0.80, 1)
    bg2 = (0.95, 0.95, 0.95, 1)
    bg3 = (0.98, 0.98, 0.98, 1)


@dataclass
class LightColorTheme(LightGrayscaleTheme):
    name = "Color, light"
    detail = (46 / 255, 194 / 255, 126 / 255, 1)  # separators, etc.; light green
    # (143/255, 240/255, 164/255, 1)  #8ff0a4 light green
    bg3 = (204 / 255, 227 / 255, 249 / 255, 1)  # text highlighting; light blue


def get_layout_height(layout) -> None:
    if isinstance(layout.spacing, int):
        spacing = layout.spacing
    else:
        spacing = layout.spacing[1]
    h_padding = layout.padding[1] + layout.padding[3]
    h_widgets = sum(c.height for c in layout.children)
    h_widgets_padding = sum(
        c.padding[1] + c.padding[3] for c in layout.children if hasattr(c, "padding")
    )
    h_spacing = spacing * (len(layout.children) - 1)
    return h_padding + h_widgets + h_widgets_padding + h_spacing


def hide_widget(wid, do_hide=True):
    # logging.debug(f"GUI: hide {wid.hostname}={do_hide}")
    if hasattr(wid, "opacity_prev") and not do_hide:
        wid.opacity = wid.opacity_prev
        del wid.opacity_prev
    elif do_hide:
        wid.opacity_prev = wid.opacity
        wid.opacity = 0


def location_to_rel_pos(location: str) -> list:
    coords = location.split(",")
    pos = (int(coords[0]), LOCATION_MAX_Y - int(coords[1]))
    return pos_to_rel_pos(pos)


def pos_to_rel_pos(pos) -> list:
    return [pos[0] / LOCATION_MAX_X, pos[1] / LOCATION_MAX_Y]
