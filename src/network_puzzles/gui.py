from kivy.app import App
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from pathlib import Path

from . import messages
from .gui_base import AppExceptionHandler
from .gui_base import Device
from .gui_base import Link
from .gui_labels import ThemedLabel  # noqa: F401, imported here for KV file access
from .gui_layouts import SelectableRecycleBoxLayout  # noqa: F401, imported here for KV file access
from .gui_popups import PuzzleChooserPopup


class NetworkPuzzlesApp(App):
    DARKEST_COLOR = (0.10, 0.10, 0.10, 1)
    DARKER_COLOR = (0.15, 0.15, 0.15, 1)
    DARK_COLOR = (0.20, 0.20, 0.20, 1)
    MEDIUM_COLOR = (0.50, 0.50, 0.50, 1)
    LIGHT_COLOR = (0.80, 0.80, 0.80, 1)
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

        self.devices = []
        self.links = []
        self.filtered_puzzles = []
        self.filters = []
        self.selected_puzzle = None
        self.ct = 1

    def add_device(self, device_inst):
        self.devices.append(device_inst)
        self.root.ids.layout.add_widget(device_inst)

    def add_link(self, link_inst):
        self.links.append(link_inst)
        self.root.ids.layout.add_widget(link_inst)

    def add_terminal_line(self, line):
        if not line.endswith('\n'):
            line += '\n'
        self.root.ids.terminal.text += f"{line}"

    def clear_puzzle(self):
        """Remove any existing widgets in the puzzle layout."""
        for device in self.devices:
            self.remove_device(device)
        for link in self.links:
            self.remove_link(link)
        self.devices = []
        self.links = []
        self.selected_puzzle = None
        # Remove any remaining child widgets from puzzle layout.
        self.root.ids.layout.clear()

    def get_device_by_id(self, device_id):
        # This returns the gui.Device widget, which is different from
        # puzzle.deviceFromId, which returns a data dict.
        for w in self.root.ids.layout.children:
            if w.data.get('uniqueidentifier') == device_id:
                return w

    def on_checkbox_activate(self, inst):
        if inst.state == 'down':
            print(f"{inst.name} is checked")
            self.filters.append(inst.name)
        elif inst.state == 'normal':
            self.filters.remove(inst.name)
        # TODO: Refresh the puzzle list using the updated self.filters.
        # I have the checkbox instance, but it doesn't seem to contain any
        # reference to the parent popup window, whose PuzzlesRecView I need to
        # update.
        self.update_puzzle_list(inst.get_popup())

    def on_help(self):
        print('help clicked')

    def on_menu(self):
        print('menu clicked')

    def on_puzzle_chooser(self):
        PuzzleChooserPopup().open()

    def remove_device(self, device_inst):
        self.root.ids.layout.remove_widget(device_inst)
        self.devices.remove(device_inst)

    def remove_link(self, link_inst):
        self.root.ids.layout.remove_widget(link_inst)
        self.links.remove(link_inst)

    def setup_links(self, *args):
        # self.link_data is typically a list of links, but it's occasionally
        # a one-link dict.
        if isinstance(self.link_data, dict):
            self.add_link(Link(self.link_data))
        elif isinstance(self.link_data, list):
            for link in self.link_data:
                self.add_link(Link(link))

        # Remove and re-add Devices so that they're on top of Links.
        for device in self.devices:
            self.remove_device(device)
            self.add_device(device)

    def setup_puzzle(self, puzzle_data):
        self.clear_puzzle()
        if puzzle_data is None:
            print("No puzzle selected.")
            return

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

        # self.device_data is typically a list of devices, but it's occasionally
        # a one-device dict.
        if isinstance(self.device_data, dict):
            self.add_device(Device(self.device_data))
        elif isinstance(self.device_data, list):
            for dev in self.device_data:
                self.add_device(Device(dev))
        
        if self.link_data:
            # Add links one tick after devices so that devices are positioned first.
            Clock.schedule_once(self.setup_links)

    def update_puzzle_list(self, popup=None):
        # TODO: At the moment self.filter is a list that can include 0 or more
        # puzzle names, but getAllPuzzleNames only accepts a single string. So
        # we currenly just accept the first item in the list as the filter.
        pfilter = None
        if isinstance(self.filters, list) and len(self.filters) > 0:
            pfilter = f"{self.filters[0]}"
        elif isinstance(self.filters, str):
            pfilter = self.filters
        self.filtered_puzzlelist = sorted(self.ui.getAllPuzzleNames(pfilter))
        if popup:
            popup.ids.puzzles_view.update_data()

    def _test(self, *args, **kwargs):
        self.setup_puzzle(self.ui.load_puzzle('5'))
        # raise NotImplementedError


class PuzzleLayout(RelativeLayout):
    def clear(self):
        for w in self.children:
            self.remove_widget(w)


