import traceback
from kivy.app import App
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
from kivy.uix.widget import Widget

from .. import device
from .. import link
from .. import parser
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
        self.app = App.get_running_app()


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
        self.app = App.get_running_app()

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
        self.app = App.get_running_app()
        self.data = init_data
        if self.data is None:
            self.new()

        self.base = device.Device(self.data)
        
        self.commands = ["Ping pc0 router0", "Power on/off", f"Replace {self.base.hostname}", "Add UPS"]
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
        parser.parse(cmd_string)

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
        img = devices.get(self.data.get('mytype')).get('img')
        if img is None:
            raise TypeError(f"Unhandled device type: {self.data.get('mytype')}")
        self.button.background_normal = str(self.app.IMAGES / img)

    def _set_pos(self):
        self.coords = location_to_coords(self.data.get('location'))
        self.pos_hint = {'center': self.coords}


class Link(Widget):
    end = ListProperty(None)
    start = ListProperty(None)

    def __init__(self, init_data=None, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.data = init_data
        if self.data is None:
            self._set_uid()
            self.set_link_type()
            self.set_start_nic()
            self.set_end_nic()

        self.base = link.Link(self.data)

        self._set_points()

        self.background_normal = ''
        with self.canvas:
            Color(rgba=self.app.DARK_COLOR)
            Line(points=(*self.start, *self.end), width=2)

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
        start_dev = self.app.get_device_by_id(self.data.get('SrcNic').get('hostid'))
        self.start = start_dev.button.center
        end_dev = self.app.get_device_by_id(self.data.get('DstNic').get('hostid'))
        self.end = end_dev.button.center


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