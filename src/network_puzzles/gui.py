from kivy.app import App
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import BooleanProperty
from kivy.properties import StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.relativelayout import RelativeLayout
from pathlib import Path

from . import messages
from . import session
from .gui_base import AppExceptionHandler
from .gui_base import Device
from .gui_base import Link
from .gui_base import AppPopup


class NetworkPuzzlesApp(App):
    DARKEST_COLOR = (0.1, 0.1, 0.1, 1)
    DARK_COLOR = (0.15, 0.15, 0.15, 1)
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
        self.filters = []
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
        # Remove any existing widgets in the layout.
        self.root.ids.layout.clear()

        puzzle_id = puzzle_data.get('uniqueidentifier')
        # Get puzzle text from localized messages, if possible, but fallback to
        # English text in JSON data.
        puzzle_messages = messages.puzzles.get(puzzle_id)
        if puzzle_messages:
            title = puzzle_messages.get('title')
            message = puzzle_messages.get('message')
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

    def get_device_by_id(self, device_id):
        # This returns the gui.Device widget, which is different from
        # puzzle.deviceFromId, which returns a data dict.
        for w in self.root.ids.layout.children:
            if w.data.get('uniqueidentifier') == device_id:
                return w

    def on_checkbox_activate(self, inst):
        if inst.state == 'down':
            self.filters.append(inst.name)
        elif inst.state == 'normal':
            self.filters.remove(inst.name)

    def _setup_links(self, *args):
        if self.link_data:  # not every puzzle has links
            for lin in self.link_data:
                w = Link(lin)
                self.links.append(w)
                self.root.ids.layout.add_widget(w)
            # Remove and re-add Devices so that they're on top of Links.
            for d in self.devices:
                self.root.ids.layout.remove_widget(d)
                self.root.ids.layout.add_widget(d)

    def _test(self, *args, **kwargs):
        self.setup_puzzle(self.ui.load_puzzle('5'))
        print(session.__dict__)
        # raise NotImplementedError


class PuzzleLayout(RelativeLayout):
    def clear(self):
        app = App.get_running_app()
        app.links = []
        app.devices = []
        for w in self.children:
            self.remove_widget(w)


class PuzzleChooserPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_dismiss(self):
        self.app.selected_puzzle = None

    def on_load(self):
        session.puzzle = self.app.selected_puzzle
        self.app.setup_puzzle(session.puzzle)
        self.dismiss()


class SelectableRecycleBoxLayout(
    FocusBehavior,
    LayoutSelectionBehavior,
    RecycleBoxLayout
):
    ''' Adds selection and focus behaviour to the view. '''
    pass


class ThemedCheckBox(CheckBox):
    name = StringProperty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()

    def on_activate(self):
        self.app.on_checkbox_activate(self)


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
