import traceback
from kivy.app import App
from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.properties import BooleanProperty
from kivy.properties import ListProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget
from pathlib import Path

from . import device
from . import link
from . import messages
from . import session


class NetworkPuzzlesApp(App):
    DARK_COLOR = (0.1, 0.1, 0.1, 1)
    LIGHT_COLOR = (0.8, 0.8, 0.8, 1)
    LIGHTER_COLOR = (0.95, 0.95, 0.95, 1)
    LIGHTEST_COLOR = (0.98, 0.98, 0.98, 1)
    Window.clearcolor = LIGHTER_COLOR
    Window.size = (1600, 720)  # 20:9 aspect ratio
    IMAGES = Path(__file__).parent / 'resources' / 'images'

    def __init__(self, ui, **kwargs):
        super().__init__(**kwargs)
        ExceptionManager.add_handler(AppExceptionHandler())
        self.ui = ui
        self.app_title = self.ui.TITLE
        self.title = self.app_title
        self.selected_puzzle = None
        self.ct = 1

    def add_terminal_line(self, line):
        if not line.endswith('\n'):
            line += '\n'
        self.root.ids.terminal.text += f"{line}"

    def on_help(self):
        print('help clicked')

    def on_menu(self):
        print('menu clicked')

    def on_puzzle_chooser(self):
        PuzzleChooserPopup().open()

    def setup_puzzle(self, puzzle_data):
        puzzle_id = puzzle_data.get('uniqueidentifier')
        # Get puzzle text from localized messages, if possible, but fallback to
        # English text in JSON data.
        puzzle_messages = messages.puzzles.get(puzzle_id)
        if puzzle_messages:
            title = puzzle_messages.get('title')
            title = puzzle_messages.get('message')
        else:
            title = puzzle_data.get('en_title', '<no title>')
            message = puzzle_data.get('en_message', '<no message>')
        
        self.title += f": {title}"
        self.root.ids.info.text = message

        self.device_data = puzzle_data.get('device')
        self.link_data = puzzle_data.get('link')
        self.devices = []
        self.links = []

        for dev in self.device_data:
            w = Device(dev)
            self.devices.append(w)
            self.root.ids.layout.add_widget(w)
        # Add links one tick after devices so that devices are positioned first.
        Clock.schedule_once(self._setup_links)

    def _setup_links(self, *args):
        for lin in self.link_data:
            w = Link(lin)
            self.links.append(w)
            self.root.ids.layout.add_widget(w)
        # Remove and re-add Devices so that they're on top of Links.
        for d in self.devices:
            self.root.ids.layout.remove_widget(d)
            self.root.ids.layout.add_widget(d)

    def get_device_by_id(self, device_id):
        # This returns the gui.Device widget, which is different from
        # puzzle.deviceFromId, which returns a data dict.
        for w in self.root.ids.layout.children:
            if w.data.get('uniqueidentifier') == device_id:
                return w

    def _test(self, *args, **kwargs):
        self.setup_puzzle(self.ui.load_puzzle('5'))
        print(session.__dict__)
        # raise NotImplementedError


class AppExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        ExceptionPopup(message=traceback.format_exc()).open()
        # return ExceptionManager.PASS
        return ExceptionManager.RAISE


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

class PuzzleChooserPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_dismiss(self):
        self.app.selected_puzzle = None

    def on_load(self):
        session.puzzle = self.app.selected_puzzle
        self.app.setup_puzzle(session.puzzle)
        self.dismiss()


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


class SelectableRecycleBoxLayout(
    FocusBehavior,
    LayoutSelectionBehavior,
    RecycleBoxLayout
):
    ''' Adds selection and focus behaviour to the view. '''
    pass

class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

class SelectableLabel(RecycleDataViewBehavior, ThemedLabel):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        name = rv.data[index].get('text')
        self.selected = is_selected
        if is_selected:
            self.app.selected_puzzle = self.app.ui.load_puzzle(name)

class AppRecView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

class PuzzlesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter = None
        self.data = [{'text': n} for n in sorted(self.app.ui.getAllPuzzleNames(self.filter))]
