import traceback
from kivy.app import App
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.widget import Widget

from . import device
from . import link
from . import parser
from .gui_buttons import CommandButton
from .gui_labels import ThemedLabel
from .gui_layouts import ThemedBoxLayout
from .gui_popups import ActionsPopup
from .gui_popups import ExceptionPopup


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
        # print(f"{self.data=}")
        if self.data is None:
            self._set_uid()
            self.set_type()
            self.set_location()
            self.set_hostname()

        self.base = device.Device(self.data)
        
        self.actions = ["Ping other host", "Power on/off", f"Replace {self.base.hostname}", "Add UPS"]
        self.orientation = 'vertical'
        self.spacing = 0
        self._set_pos()  # sets self.coords and self.pos_hint
        self.size_hint = (0.08, 0.20)
        self.label_hostname = ThemedLabel(text=self.base.hostname, size_hint=[1, 1], halign='center')
        self.button = Button(size_hint_y=2)
        self._set_image()
        # TODO: Button to cycle through showing hostname and/or IPs?
        self.add_widget(self.button)
        self.add_widget(self.label_hostname)

    def callback(self, cmd_string):
        parser.parse(cmd_string)

    def on_press(self):
        self._build_popup().open()

    def set_hostname(self):
        raise NotImplementedError

    def set_location(self):
        raise NotImplementedError

    def set_type(self):
        raise NotImplementedError

    def _set_uid(self):
        raise NotImplementedError

    def _build_popup(self):
        # Setup the content.
        content = GridLayout(cols=1, spacing=dp(5))
        for command in self.actions:
            content.add_widget(CommandButton(self.callback, command))
        content.size_hint_y = None
        content.height = get_layout_height(content)
        # Setup the Popup.
        popup = ActionsPopup(content=content, title=self.base.hostname)
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
        img = ''
        match self.data.get('mytype'):
            case 'net_hub':
                img = 'Hub.png'
            case 'net_switch':
                img = 'Switch.png'
            case 'pc':
                img = 'PC.png'
            case 'laptop':
                img = 'Laptop.png'
            case 'router':
                img = 'Router.png'
            case 'firewall':
                img = 'firewall.png'
            case 'copier':
                img = 'Copier.png'
            case 'cellphone':
                img = 'cellphone.png'
            case 'fluorescent':
                img = 'fluorescent.png'
            case 'ip_phone':
                img = 'ip_phone.png'
            case 'microwave':
                img = 'microwave.png'
            case 'printer':
                img = 'Printer.png'
            case 'server':
                img = 'Server.png'
            case 'tablet':
                img = 'tablet.png'
            case 'tree':
                img = 'tree.png'
            case 'wap':
                img = 'WAP.png'
            case 'wbridge':
                img = 'WBridge.png'
            case 'wrepeater':
                img = 'WRepeater.png'
            case 'wrouter':
                img = 'WRouter.png'
            case _:
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
        # print(f"{self.data=}")
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
    # print(f"{layout=}; {h_padding=}; {h_widgets=}; {h_widgets_padding=}; {h_spacing=}")
    return h_padding + h_widgets + h_widgets_padding + h_spacing


def location_to_coords(location: str) -> list:
    coords = location.split(',')
    return [int(coords[0])/900, 1 - int(coords[1])/850]