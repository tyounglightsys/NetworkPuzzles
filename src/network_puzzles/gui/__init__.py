import platform
from kivy.app import App
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.metrics import sp
from kivy.uix.relativelayout import RelativeLayout
from pathlib import Path

from .. import messages
from .. import session
from .base import AppExceptionHandler
from .base import Device
from .base import Link
from .base import Packet
from .base import NETWORK_ITEMS
from .base import LightColorTheme
from .buttons import MenuButton
from .layouts import AppMenu
from .popups import PuzzleChooserPopup


class NetworkPuzzlesApp(App):
    # explicit sizes
    BUTTON_MAX_H = dp(48)
    BUTTON_FONT_SIZE = sp(24)
    PACKET_DIMS = (dp(15), dp(15))

    # file paths
    IMAGES = Path(__file__).parents[1] / 'resources' / 'images'

    def __init__(self, ui, **kwargs):
        # Set session `app` variable.
        session.app = self

        # Set window size for desktop systems.
        if platform.system() not in ['Android', 'iOS']:
            Window.size = (1600, 720)  # 20:9 aspect ratio

        super().__init__(**kwargs)
        ExceptionManager.add_handler(AppExceptionHandler())
        self.ui = ui
        self.app_title = self.ui.TITLE
        self.title = self.app_title
        self.theme = LightColorTheme
        Window.clearcolor = self.theme.bg2

        self.devices = []
        self.links = []
        self.filtered_puzzles = []
        self.filters = []
        self.selected_puzzle = None

        self.new_item_menu = None
        self.new_infra_device_menu = None
        self.new_user_device_menu = None
        self.ct = 1
        self.packet_delay = 0.02  # refresh rate in seconds
        self.prev_packets = []  # packets to remove from last refresh

        Clock.schedule_interval(self._update_packets, self.packet_delay)

    def add_device(self, device_inst=None):
        # TODO: If device_inst not given, require user to choose device type
        # on the screen to instantiate a new device.
        if device_inst is None:
            device_inst = Device()

        self.devices.append(device_inst)
        self.root.ids.layout.add_widget(device_inst)

    def add_link(self, link_inst=None):
        # TODO: If link_inst not given, require user to tap on start and end
        # devices on the screen to instantiate a new link.
        if link_inst is None:
            # link_inst = Link()
            raise NotImplementedError

        self.links.append(link_inst)
        # Add link to z-index = 99 to ensure it's drawn under device.
        self.root.ids.layout.add_widget(link_inst, 99)

    def add_terminal_line(self, line):
        if not line.endswith('\n'):
            line += '\n'
        self.root.ids.terminal.text += f"{line}"

    def clear_puzzle(self):
        """Remove any existing widgets in the puzzle layout."""
        self.devices = []
        self.links = []
        self.selected_puzzle = None
        self.reset_display()

    def get_widget_by_uid(self, uid):
        # This returns the gui widget, which is different from
        # the puzzle JSON object.
        for w in self.root.ids.layout.children:
            if hasattr(w, 'base') and hasattr(w.base, 'json') and w.base.json.get('uniqueidentifier') == uid:
                return w

    def last_link_index(self):
        last_index = 0
        for w in self.root.ids.layout.children:
            if w.__class__.__name__ == 'Link':
                last_index = max([self.root.ids.layout.children.index(w), last_index])
        return last_index

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
        raise NotImplementedError

    def on_language(self):
        raise NotImplementedError

    def on_new_infra_device(self, inst):
        # Open "tray" to select from infrastructure devices.
        devices = NETWORK_ITEMS.get('devices').get('infrastructure')
        if self.new_infra_device_menu is None:
            choices = []
            for choice in devices.values():
                choice['cb'] = Device
                choice['orientation'] = 'horizontal'
                choices.append(choice)
            self.new_infra_device_menu = AppMenu(
                anchor_pos=inst.pos,
                choices=choices,
            )
        self._toggle_tray(self.new_infra_device_menu)

    def on_new_item(self, inst):
        # Open "tray" to select item type, set its properties, etc.
        if self.new_item_menu is None:
            choices = [
                {'img': 'link.png', 'cb': self.add_link},
                {'img': 'Switch.png', 'cb': self.on_new_infra_device},
                {'img': 'PC.png', 'cb': self.on_new_user_device},
            ]
            self.new_item_menu = AppMenu(
                anchor_pos=inst.pos,
                choices=choices,
                orientation='vertical',
            )
        subtrays = [
            self.new_infra_device_menu,
            self.new_user_device_menu,
        ]
        self._toggle_tray(self.new_item_menu, subtrays=subtrays)

    def on_new_user_device(self, inst):
        # Open "tray" to select from user devices.
        devices = NETWORK_ITEMS.get('devices').get('user')
        if self.new_user_device_menu is None:
            choices = []
            for choice in devices.values():
                choice['cb'] = Device
                choice['orientation'] = 'horizontal'
                choices.append(choice)
            self.new_user_device_menu = AppMenu(
                anchor_pos=inst.pos,
                choices=choices,
            )
        self._toggle_tray(self.new_user_device_menu)

    def on_save(self):
        raise NotImplementedError

    def on_start(self):
        self._add_new_item_button()

    def on_puzzle_chooser(self):
        PuzzleChooserPopup().open()

    def remove_device(self, device_inst):
        self.root.ids.layout.remove_widget(device_inst)
        self.devices.remove(device_inst)

    def remove_link(self, link_inst):
        self.root.ids.layout.remove_widget(link_inst)
        self.links.remove(link_inst)

    def reset_display(self):
        """Clear display without clearing loaded puzzle data."""
        self.title = self.app_title
        # Remove any remaining child widgets from puzzle layout.
        self.root.ids.layout.clear_widgets()
        # Replace the "+" button for adding new items.
        self._add_new_item_button()

    def setup_links(self, *args):
        # self.link_data is typically a list of links, but it's occasionally
        # a one-link dict.
        if isinstance(self.link_data, dict):
            self.add_link(Link(self.link_data))
        elif isinstance(self.link_data, list):
            for link in self.link_data:
                self.add_link(Link(link))

    def setup_puzzle(self, puzzle_data=None):
        self.reset_display()
        if puzzle_data is None:
            puzzle_data = session.puzzle.json

        # Combine level & sortorder to get unique message ID.
        puzzle_msg_id = f"{puzzle_data.get('level')}.{puzzle_data.get('sortorder')}"
        # Get puzzle text from localized messages, if possible, but fallback to
        # English text in JSON data.
        puzzle_messages = messages.puzzles.get(puzzle_msg_id)
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
            # Add links one tick after devices so that devices are positioned
            # first, since links' positions depend on devices' positions.
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

    def _add_new_item_button(self, *args):
        self.new_item_button = MenuButton(
            props={'text': "+", 'cb': self.on_new_item,},
            pos_hint={'x': 0.005, 'top': 0.99},
        )
        self.root.ids.layout.add_widget(self.new_item_button)

    def _close_tray(self, tray):
        tray.close()
        self.root.ids.layout.remove_widget(tray)

    def _open_tray(self, tray):
        self.root.ids.layout.add_widget(tray)
        tray.open()        

    def _toggle_tray(self, tray, subtrays=None):
        # Open tray, if not open.
        if tray not in self.root.ids.layout.children:
            self._open_tray(tray)
        # Close tray and subtrays if not closed.
        else:
            # First make sure submenu trays aren't open.
            if subtrays:
                for subtray in subtrays:
                    if subtray is not None:
                        self._close_tray(subtray)
            self._close_tray(tray)


    def _update_packets(self, dt):
        # Update backend packet info.
        self.ui.process_packets(self.packet_delay)

        # Remove existing packets from layout.
        while self.prev_packets:
            self.root.ids.layout.remove_widget(self.prev_packets.pop())

        # packet draw index needs to be above link lines but below devices.
        packet_idx = self.last_link_index() - 1

        # Add new packet locations to layout.
        for p in session.packetlist:
            link_data = session.puzzle.link_from_name(p.get('packetlocation'))
            link = self.get_widget_by_uid(link_data.get('uniqueidentifier'))
            prog = p.get('packetDistance')
            if p.get('packetDirection') == 2:
                prog = 100 - prog
            x, y = link.get_progress_pos(prog)
            packet = Packet(pos=(x - self.PACKET_DIMS[0] / 2, y - self.PACKET_DIMS[1] / 2))
            self.root.ids.layout.add_widget(packet, packet_idx)
            self.prev_packets.append(packet)

    def _test(self, *args, **kwargs):
        raise NotImplementedError


class PuzzleLayout(RelativeLayout):
    pass


