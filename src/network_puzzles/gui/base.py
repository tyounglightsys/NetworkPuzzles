# import logging
import traceback
from dataclasses import dataclass
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.recycleview import RecycleView
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from typing import Tuple

from .. import link
from .. import session
from .popups import ExceptionPopup
from .popups import LinkPopup


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


class PuzzlesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.update_puzzle_list()
        self.data = {}
        self.update_data()

    def update_data(self):
        self.data = [{"text": n} for n in self.app.filtered_puzzlelist]


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


class Link(Widget):
    end = ListProperty(None)
    start = ListProperty(None)

    def __init__(self, init_data=None, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.base = link.Link(init_data)

        self._set_points()
        self._set_size_and_pos()

        self.background_normal = ""
        self._draw_line()

    @property
    def hostname(self):
        if hasattr(self, "base"):
            return self.base.hostname
        else:
            return None

    @property
    def hosts(self):
        return [self.app.get_widget_by_hostname(h) for h in self.base.hosts]

    @property
    def uid(self):
        if hasattr(self, "base") and hasattr(self.base, "json"):
            return self.base.json.get("uniqueidentifier")
        else:
            return None

    def _draw_line(self):
        self.canvas.clear()
        with self.canvas:
            Color(rgba=self.app.theme.fg1)
            Line(points=(*self.start, *self.end), width=2)

    def edit(self):
        # TODO: Add Edit Link Popup.
        raise NotImplementedError

    def get_progress_pos(self, progress):
        dx = progress * (self.end[0] - self.start[0]) / 100
        dy = progress * (self.end[1] - self.start[1]) / 100
        return (self.start[0] + dx, self.start[1] + dy)

    def hide(self, do_hide=True):
        hide_widget(self, do_hide)

    def move_connection(self, dev):
        # Update link properties.
        if self.hostname.startswith(dev.hostname):
            self._set_startpoint(dev)
        elif self.hostname.endswith(dev.hostname):
            self._set_endpoint(dev)
        self._set_size_and_pos()
        # Redraw the link line.
        self._draw_line()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            LinkPopup(self).open()
            return True

    def set_end_nic(self):
        # TODO: Set hostname once DstNic is set as:
        # "SrcNicHostname_link_DstNicHostname"
        raise NotImplementedError

    def set_link_type(self):
        # Set one of: 'broken', 'normal', 'wireless'
        raise NotImplementedError

    def set_start_nic(self):
        raise NotImplementedError

    def _set_uid(self):
        raise NotImplementedError

    def _set_endpoint(self, end_dev=None):
        if end_dev is None:
            end_dev = self.app.get_widget_by_uid(
                self.base.json.get("DstNic").get("hostid")
            )
        self.end = end_dev.button.center

    def _set_startpoint(self, start_dev=None):
        if start_dev is None:
            start_dev = self.app.get_widget_by_uid(
                self.base.json.get("SrcNic").get("hostid")
            )
        self.start = start_dev.button.center

    def _set_points(self):
        self._set_startpoint()
        self._set_endpoint()

    def _set_size_and_pos(self):
        # Set pos.
        self.x = min([self.start[0], self.end[0]])
        self.y = min([self.start[1], self.end[1]])
        # Set size.
        self.size_hint = (None, None)
        w = self.start[0] - self.end[0]
        if w < 0:
            w = -1 * w
        self.width = w
        h = self.start[1] - self.end[1]
        if h < 0:
            h = -1 * h
        self.height = h


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
