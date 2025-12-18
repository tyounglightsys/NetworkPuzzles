import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget

from .. import session
from .popups import ExceptionPopup

# Size limits
BUTTON_MAX_H = dp(32)
BUTTON_FONT_SIZE = sp(24)
DEVICE_BUTTON_MAX_H = BUTTON_MAX_H * 1.25
PACKET_DIMS = (dp(15), dp(15))

IMAGES_DIR = Path(__file__).parents[1] / "resources" / "images"
# NOTE: Puzzle size is nominally 900x850. The PADDING is applied to all sides of
# the puzzle layout area, and it should be large enough to accommodate 1/2 the
# height of a device widget, which includes button + label + spacing & padding.
PADDING = DEVICE_BUTTON_MAX_H
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


class ThemedCheckBox(CheckBox):
    name = StringProperty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def app(self):
        return session.app

    def get_popup(self):
        for win in self.get_parent_window().children:
            # Only Popup widget has 'content' attribute.
            if hasattr(win, "content"):
                return win

    def on_activate(self):
        self.app.on_checkbox_activate(self)


class HelpHighlight(Widget):
    def __init__(self, base=None, **kwargs):
        self.base = base
        super().__init__(**kwargs)


class LockEmblem(Widget):
    def __init__(self, base=None, **kwargs):
        self.base = base
        super().__init__(**kwargs)


class HelpSlider(Slider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = HelpLevel.FULL
        self.bind(value=self.app.update_help)

    @property
    def app(self):
        return session.app


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


def get_effective_size(size):
    return (size[0] - 2 * PADDING, size[1] - 2 * PADDING)


def get_layout_height(layout) -> int:
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


def location_to_pos(location: iter, size) -> tuple:
    """Converts EduNetworkBuilder's location coords to relative layout's position."""
    if len(location) != 2:
        raise ValueError(f"GUI: location length != 2: {location}")
    # Get relative location (invert y-coord).
    # logging.debug(f"GUI: input location: {location}")
    effective_rel_pos = (
        location[0] / LOCATION_MAX_X,
        1 - (location[1] / LOCATION_MAX_Y),
    )
    # logging.debug(f"GUI: effective area rel pos: {effective_rel_pos}")
    # Calculate proportial pos within non-padded puzzle area.
    effective_pos = rel_pos_to_pos(effective_rel_pos, get_effective_size(size))
    # logging.debug(f"GUI: effective area pos: {effective_pos}")
    # Calculate abs pos by taking padding into account.
    pos = (PADDING + effective_pos[0], PADDING + effective_pos[1])
    logging.debug(f"GUI: {location=} -> {pos=}")
    return pos


def location_to_rel_pos(location: iter, size) -> tuple:
    if len(location) != 2:
        raise ValueError(f"GUI: location length != 2: {location}")
    pos = location_to_pos(location, size)
    rel_pos = pos_to_rel_pos(pos, size)
    logging.debug(f"GUI: {location=} -> {rel_pos=}")
    return rel_pos


def pos_to_location(pos, size) -> tuple:
    """Converts relative layout's position to EduNetworkBuilder's location coords."""
    # logging.debug(f"GUI: input pos: {pos}")
    x = pos[0]
    y = pos[1]

    # Limit x and y to non-padded values.
    if x < PADDING:
        x = PADDING
    if x > size[0] - PADDING:
        x = size[0] - PADDING
    if y < PADDING:
        y = PADDING
    if y > size[1] - PADDING:
        y = size[1] - PADDING
    # logging.debug(f"GUI: limited pos: ({x}, {y})")

    # Subtract padding to get pos in effective puzzle area.
    effective_pos = (x - PADDING, y - PADDING)
    # logging.debug(f"GUI: effective area pos: {effective_pos}")
    # Divide by effective area l/w to get relative pos in effective area.
    effective_rel_pos = pos_to_rel_pos(effective_pos, get_effective_size(size))
    # logging.debug(f"GUI: effective area rel pos: {effective_rel_pos}")
    # Multiply by location max values to get location value (invert y-axis).
    loc = (
        round(effective_rel_pos[0] * LOCATION_MAX_X),
        round((1 - effective_rel_pos[1]) * LOCATION_MAX_Y),
    )
    logging.debug(f"GUI: {pos=} -> {loc=}")
    return loc


def pos_to_rel_pos(pos, size) -> tuple:
    """Convert absolute position to relative decimal values from 0 to 1."""
    rel_pos = (pos[0] / size[0], pos[1] / size[1])
    # logging.debug(f"GUI: {size=}; {pos=} -> {rel_pos=}")
    return rel_pos


def rel_pos_to_pos(rel_pos, size) -> tuple:
    """Convert relative decimal value position to absolute position."""
    pos = (rel_pos[0] * size[0], rel_pos[1] * size[1])
    # logging.debug(f"GUI: {rel_pos=} -> {pos=}; {size=}")
    return pos


def print_layout_info(app):
    # Layout debug logging.
    layout = app.root.ids.layout
    logging.debug(f"GUI: {layout.__class__.__name__} corner: {layout.pos}")
    logging.debug(f"GUI: {layout.__class__.__name__} size: {layout.size}")
    w = layout.size[0] - 2 * PADDING
    h = layout.size[1] - 2 * PADDING
    x = layout.x + PADDING
    y = layout.y + PADDING
    logging.debug(f"GUI: {layout.__class__.__name__} effective corner: [{x}, {y}]")
    logging.debug(f"GUI: {layout.__class__.__name__} effective size: [{w}, {h}]")
    logging.debug(f"GUI: {layout.__class__.__name__} elements:")
    for w in layout.children:
        if hasattr(w, "hostname"):
            logging.debug(
                f"GUI: - {w.__class__.__name__}/{w.hostname}: {w.center=}; {w.pos=}; {w.size=}"
            )
            if hasattr(w, "get_height"):  # layout
                logging.debug(f"GUI: -- {w.get_height()=}")
                logging.debug(f"GUI: -- {w.drag_rectangle=}")
        else:
            logging.debug(
                f"GUI: - {w.__class__.__name__}: {w.center=}; {w.pos=}; {w.size=}"
            )


def show_grid(app):
    """Add grid dots at all major intersections to verify device alignment."""
    layout = app.root.ids.layout
    logging.debug(f"GUI: {layout.size=}")
    with layout.canvas.after:
        Color(1, 0, 0)
        for x in range(0, 1000, 100):
            for y in range(0, 900, 100):
                local_pos = location_to_pos((x, y), layout.size)
                pos = layout.to_window(*local_pos, initial=False)
                logging.debug(f"GUI: loc: ({x}, {y}); abs pos: {local_pos}; pos: {pos}")
                Ellipse(pos=pos, size=(5, 5))
