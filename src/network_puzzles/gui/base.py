import traceback
from dataclasses import dataclass
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from typing import Tuple

from .. import device
from .. import link
from .. import session
from .buttons import CommandButton
from .buttons import DeviceButton
from .labels import DeviceLabel
from .layouts import ThemedBoxLayout
from .popups import CommandsPopup
from .popups import ExceptionPopup


NETWORK_ITEMS = {
    'links': {
        'link': {'img': 'link.png'},
    },
    'devices': {
        'user': {
            'cellphone': {'img': 'cellphone.png'},
            'copier': {'img': 'Copier.png'},
            'ip_phone': {'img': 'ip_phone.png'},
            'laptop': {'img': 'Laptop.png'},
            'microwave': {'img': 'microwave.png'},
            'pc': {'img': 'PC.png'},
            'printer': {'img': 'Printer.png'},
            'tablet': {'img': 'tablet.png'},
        },
        'infrastructure': {
            'firewall': {'img': 'firewall.png'},
            'fluorescent': {'img': 'fluorescent.png'},
            'net_hub': {'img': 'Hub.png'},
            'net_switch': {'img': 'Switch.png'},
            'router': {'img': 'Router.png'},
            'server': {'img': 'Server.png'},
            'tree': {'img': 'tree.png'},
            'wap': {'img': 'WAP.png'},
            'wbridge': {'img': 'WBridge.png'},
            'wrepeater': {'img': 'WRepeater.png'},
            'wrouter': {'img': 'WRouter.png'},
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
        self.data = [{'text': n} for n in self.app.filtered_puzzlelist]


class ThemedCheckBox(CheckBox):
    name = StringProperty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app

    def get_popup(self):
        for win in self.get_parent_window().children:
            # Only Popup widget has 'content' attribute.
            if hasattr(win, 'content'):
                return win

    def on_activate(self):
        self.app.on_checkbox_activate(self)


class Device(ThemedBoxLayout):
    def __init__(self, init_data=None, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.base = device.Device(init_data)
                    
        self.commands = [
            f"Ping {self.base.hostname} router0",
            f"Set {self.base.hostname} power off",
        ]
        self.commands.extend(device.commands_from_tests(self.base.hostname))
        self.orientation = 'vertical'
        self.spacing = 0
        self._set_pos()  # sets self.coords and self.pos_hint
        self.size_hint = (0.08, 0.20)
        self.label_hostname = DeviceLabel(text=self.base.hostname)
        self.button = DeviceButton(callback=self.on_press)
        self._set_image()
        # TODO: Button to cycle through showing hostname and/or IPs?
        self.add_widget(self.button)
        self.add_widget(self.label_hostname)

    def callback(self, cmd_string):
        self.app.ui.parse(cmd_string)

    def new(self):
        raise NotImplementedError
        self._set_uid()
        self.set_type()
        self.set_location()
        self.set_hostname()

    def on_press(self):
        self._build_commands_popup().open()

    def set_hostname(self):
        raise NotImplementedError

    def set_location(self):
        raise NotImplementedError

    def set_type(self):
        raise NotImplementedError

    def _set_uid(self):
        raise NotImplementedError

    def _build_commands_popup(self):
        # Setup the content.
        content = GridLayout(cols=1, spacing=dp(5))
        for command in self.commands:
            content.add_widget(CommandButton(self.callback, command))
        content.size_hint_y = None
        content.height = get_layout_height(content)
        # Setup the Popup.
        popup = CommandsPopup(content=content, title=self.base.hostname)
        rootgrid = popup.children[0]
        box = rootgrid.children[0]
        grid = box.children[0]
        grid.size_hint_y = None
        grid.height = get_layout_height(grid)
        box.size_hint_y = None
        box.height = get_layout_height(box)
        rootgrid.size_hint_y = None
        rootgrid.height = get_layout_height(rootgrid)
        popup.height = rootgrid.height + dp(24)  # account for undocumented padding
        return popup

    def _set_image(self):
        devices = NETWORK_ITEMS.get('devices').get('user') | NETWORK_ITEMS.get('devices').get('infrastructure')
        img = devices.get(self.base.json.get('mytype')).get('img')
        if img is None:
            raise TypeError(f"Unhandled device type: {self.base.json.get('mytype')}")
        self.button.background_normal = str(self.app.IMAGES / img)

    def _set_pos(self):
        self.coords = location_to_coords(self.base.json.get('location'))
        self.pos_hint = {'center': self.coords}


class Link(Widget):
    end = ListProperty(None)
    start = ListProperty(None)

    def __init__(self, init_data=None, **kwargs):
        super().__init__(**kwargs)
        self.app = session.app
        self.base = link.Link(init_data)

        self._set_points()

        self.background_normal = ''
        with self.canvas:
            Color(rgba=self.app.theme.fg1)
            Line(points=(*self.start, *self.end), width=2)

    def get_progress_pos(self, progress):
        dx = progress * (self.end[0] - self.start[0]) / 100
        dy = progress * (self.end[1] - self.start[1]) / 100
        return (self.start[0] + dx, self.start[1] + dy)

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

    def _set_points(self):
        start_dev = self.app.get_widget_by_uid(self.base.json.get('SrcNic').get('hostid'))
        self.start = start_dev.button.center
        end_dev = self.app.get_widget_by_uid(self.base.json.get('DstNic').get('hostid'))
        self.end = end_dev.button.center


class Packet(Widget):
    pass


class HelpSlider(Slider):
    pass
    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     print(self.children)


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
    name = 'Grayscale, light'
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
    detail = (46/255, 194/255, 126/255, 1)  # separators, etc.; light green
    #(143/255, 240/255, 164/255, 1)  #8ff0a4 light green
    bg3 = (204/255, 227/255, 249/255, 1)  # text highlighting; light blue


def get_layout_height(layout) -> None:
    if isinstance(layout.spacing, int):
        spacing = layout.spacing
    else:
        spacing = layout.spacing[1]
    h_padding = layout.padding[1] + layout.padding[3]
    h_widgets = sum(c.height for c in layout.children)
    h_widgets_padding = sum(c.padding[1] + c.padding[3] for c in layout.children if hasattr(c, 'padding'))
    h_spacing = spacing * (len(layout.children) - 1)
    return h_padding + h_widgets + h_widgets_padding + h_spacing


def location_to_coords(location: str) -> list:
    coords = location.split(',')
    return [int(coords[0])/900, 1 - int(coords[1])/850]