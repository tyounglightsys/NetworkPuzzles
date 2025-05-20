import traceback
from kivy.app import App
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.properties import ListProperty
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from . import device
from . import link


class Device(Button):
    def __init__(self, init_data, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.data = init_data
        self.base = device.Device(self.data)

        self._set_pos()  # sets self.coords and self.pos_hint
        self.size_hint_x = self.data.get('width')
        self.size_hint_y = self.data.get('height')
        self._set_image()

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
        self.background_normal = str(self.app.IMAGES / img)

    def _set_pos(self):
        self.coords = [int(v)/1000 for v in self.data.get('location').split(',')]
        self.pos_hint = {'center': self.coords}


class Link(Widget):
    end = ListProperty(None)
    start = ListProperty(None)

    def __init__(self, init_data, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.data = init_data
        self.base = link.Link(self.data)

        self._set_points()

        self.background_normal = ''
        with self.canvas:
            Color(rgba=self.app.DARK_COLOR)
            Line(points=(*self.start, *self.end), width=2)
    
    def _set_points(self):
        start_dev = self.app.get_device_by_id(self.data.get('SrcNic').get('hostid'))
        self.start = start_dev.center
        end_dev = self.app.get_device_by_id(self.data.get('DstNic').get('hostid'))
        self.end = end_dev.center


class AppPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

class ExceptionPopup(AppPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message
    
    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class AppExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        ExceptionPopup(message=traceback.format_exc()).open()
        # return ExceptionManager.RAISE  # kills app right away
        return ExceptionManager.PASS