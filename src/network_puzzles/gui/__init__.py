import logging

# Remove root logger b/c kivy's logger will handle all logging.
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    root_logger.removeHandler(handler)

from .. import session

if session.device_type == "desktop":
    # Disable right-click red dot.
    from kivy.config import Config

    Config.set("input", "mouse", "mouse,disable_multitouch")

# Continue with remaining imports.
from kivy.app import App
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window

from .. import messages, nettests
from .base import (
    BUTTON_FONT_SIZE,
    BUTTON_MAX_H,
    DEVICE_BUTTON_MAX_H,
    IMAGES_DIR,
    PACKET_DIMS,
    AppExceptionHandler,
    AppRecView,
    HelpHighlight,
    LightColorTheme,
    pos_to_location,
    print_layout_info,
    show_grid,
)
from .buttons import MenuButton
from .devices import ChooseNicPopup, Device
from .links import Link
from .packets import PacketManager
from .popups import PuzzleChooserPopup, PuzzleCompletePopup


class NetworkPuzzlesApp(App):
    # explicit sizes
    BUTTON_MAX_H = BUTTON_MAX_H
    BUTTON_FONT_SIZE = BUTTON_FONT_SIZE
    DEVICE_BUTTON_MAX_H = DEVICE_BUTTON_MAX_H
    PACKET_DIMS = PACKET_DIMS

    # file paths
    IMAGES = IMAGES_DIR

    def __init__(self, ui, **kwargs):
        # Set session `app` variable.
        session.app = self

        # Set device-related config.
        if session.device_type == "desktop":
            Window.minimum_width = 574
            Window.minimum_height = 270
            # Force aspect ratio through explicit resolution.
            if Window.width / Window.height < 1.7:
                Window.size = (1600, 720)
            # NOTE: Time for packet to traverse each link is:
            #   self.packet_tick_delay * 100 / self.packet_progress_rate
            # However, there's also a tick limit of ~60 Hz for kivy.
            self.packet_tick_delay = 0.02  # packet pos refresh rate in seconds
            self.packet_progress_rate = 3  # % of link traveled each tick
        else:  # mobile devices
            # Force loglevel to DEBUG.
            logger = logging.getLogger()
            logger.level = logging.DEBUG
            self.packet_tick_delay = 0.04  # packet pos refresh rate in seconds
            self.packet_progress_rate = 6  # % of link traveled each tick
        logging.debug(f"GUI: {session.device_type=}")
        logging.debug(f"GUI: {Window.size=}")

        super().__init__(**kwargs)
        ExceptionManager.add_handler(AppExceptionHandler())
        self.ui = ui
        self.app_title = self.ui.TITLE
        self.title = self.app_title
        self.theme = LightColorTheme
        Window.clearcolor = self.theme.bg2
        # Re-add puzzle widgets on resize.
        Window.bind(on_resize=self.draw_puzzle)
        # Set intial values for variables.
        self.selected_puzzle = None  # used to reset puzzle after changes
        self.reset_vars()

        self.packetmgr = PacketManager(self)
        Clock.schedule_interval(self._update_packets, self.packet_tick_delay)

    @property
    def devices(self):
        return self._get_widgets_by_class_name("Device")

    @property
    def links(self):
        return self._get_widgets_by_class_name("Link")

    @property
    def packets(self):
        return self._get_widgets_by_class_name("Packet")

    def check_puzzle(self, *args):
        """Checked at regular interval during kivy app loop."""
        if self.ui.is_puzzle_done():
            PuzzleCompletePopup().open()

    def add_device(self, devicew=None, dtype=None):
        # Ensure new item menus are closed.
        self.root.ids.layout.close_trays()
        # TODO: If device_inst not given, require user to choose device type
        # on the screen to instantiate a new device.
        if not isinstance(devicew, Device):
            if isinstance(devicew, dict):
                devicew = Device(devicew)
            elif isinstance(devicew, MenuButton):
                # Initiate new device creation sequence.
                self._new_device_type = dtype
                Clock.schedule_once(self._new_device)
                return

        # Hide invisible devices.
        if devicew.base.is_invisible:
            devicew.hide()

        # Add device to layout.
        self.root.ids.layout.add_widget(devicew)

    def add_link(self, linkw=None):
        # Ensure new item menus are closed.
        self.root.ids.layout.close_trays()

        if not isinstance(linkw, Link):
            if isinstance(linkw, dict):
                linkw = Link(linkw)
            elif isinstance(linkw, MenuButton):
                # Initiate new link creation sequence.
                Clock.schedule_once(self._new_link)
                return

        # Hide liks connected to invisible devices.
        for host in (linkw.base.src, linkw.base.dest):
            w = self.get_widget_by_hostname(host)
            if w.base.is_invisible:
                linkw.hide()

        # Add link to z-index = 99 to ensure it's drawn under devices.
        self.root.ids.layout.add_widget(linkw, 99)

    def add_terminal_line(self, line):
        if not line.endswith("\n"):
            line += "\n"
        self.root.ids.terminal.text += f"{line}"

    def draw_devices(self, *args):
        for dev in self.ui.puzzle.devices:
            self.add_device(Device(dev))

    def draw_links(self, *args):
        for link in self.ui.puzzle.links:
            if link is None:
                continue
            self.add_link(Link(link))
        self._print_stats()

    def draw_puzzle(self, *args):
        """Clear puzzle layout area; draw all elements related to current puzzle."""
        logging.debug(
            f"GUI: {self.root.ids.layout.__class__.__name__}: pos={self.root.ids.layout.pos}; size={self.root.ids.layout.size}"
        )
        if not self.ui.puzzle:
            logging.warning("GUI: No puzzle is loaded.")
            return

        self.reset_display()

        # Get puzzle text from localized messages, if possible, but fallback to
        # English text in JSON data.
        puzzle_data = self.ui.puzzle.json
        logging.debug(f"GUI: {self.ui.puzzle.uid=}")
        puzzle_messages = messages.puzzles.get(self.ui.puzzle.uid)
        if puzzle_messages:
            title = puzzle_messages.get("title")
            info = puzzle_messages.get("info")
        else:
            title = puzzle_data.get("en_title", "<no title>")
            info = puzzle_data.get("en_message", "<no message>")

        self.title += f": {title}"
        self.root.ids.info.text = f"[b]{title}[/b]\n\n{info}"
        # self.root.ids.help_slider.value = self.ui.puzzle.default_help_level

        # Add devices.
        self.draw_devices()

        # Some setup needs to be done one tick after devices, because their
        # positions depend on the devices' positions.
        Clock.schedule_once(self.update_help)
        Clock.schedule_once(self.draw_links)

    def get_first_link_index(self):
        first_index = 999
        for w in self.links:
            first_index = min([self.root.ids.layout.children.index(w), first_index])
        return first_index

    def get_widget_by_hostname(self, hostname):
        return self._get_widget_by_prop("hostname", hostname)

    def get_widget_by_uniqueidentifier(self, uid):
        return self._get_widget_by_prop("uniqueidentifier", uid)

    def on_checkbox_activate(self, inst):
        if inst.state == "down":
            self.filters.append(inst.name)
        elif inst.state == "normal":
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
        self.root.ids.layout.infra_devices_tray.toggle()

    def on_new_item(self, inst):
        self.root.ids.layout.items_tray.toggle()

    def on_new_user_device(self, inst):
        self.root.ids.layout.user_devices_tray.toggle()

    def on_puzzle_chooser(self, *args):
        PuzzleChooserPopup().open()

    def on_redo(self):
        self.ui.redo()

    def on_save(self):
        raise NotImplementedError

    def on_start(self):
        # Make widget adjustments.
        # Set initial app button states.
        self.update_undo_redo_states()
        # NOTE: Has to be added once PuzzleLayout already exists.
        self.root.ids.layout.add_items_menu_button()

        Clock.schedule_once(
            self._set_left_panel_width
        )  # buttons must update before panel
        # Open puzzle chooser if no puzzle is defined.
        if not self.ui.puzzle:
            Clock.schedule_once(self.on_puzzle_chooser)

    def on_undo(self):
        self.ui.undo()

    def remove_item(self, item):
        """Remove widget from layout by widget or item JSON data."""
        # TODO: Add parser command to also remove widget from puzzle JSON.
        widget = None
        if isinstance(item, Link) or isinstance(item, Device):
            widget = item
        elif isinstance(item, dict):
            widget = self.get_widget_by_hostname(item.get("hostname"))
        else:
            raise TypeError(f"{type(item)=}")
        if widget:
            self.root.ids.layout.remove_widget(widget)

    def reset_display(self):
        """Clear display without clearing loaded puzzle data."""
        self.title = self.app_title
        # Remove any remaining child widgets from puzzle layout.
        self.root.ids.layout.clear_widgets()
        # Redraw the "+" button for adding new items.
        self.root.ids.layout.add_items_menu_button()

    def reset_vars(self):
        # Set variables to intial values.
        self.filtered_puzzles = []
        self.filters = []

        # Delete temporary variables.
        if hasattr(self, "new_device_data"):
            del self.new_device_data
        if hasattr(self, "new_link_data"):
            del self.new_link_data
        if hasattr(self, "chosen_device"):
            del self.chosen_device
        if hasattr(self, "chosen_nic"):
            del self.chosen_nic
        if hasattr(self, "chosen_pos"):
            del self.chosen_pos

        # Cancel scheduled functions.
        Clock.unschedule(self._new_device)
        Clock.unschedule(self._new_link)

    def setup_puzzle(self, *args):
        self.reset_vars()
        self.ui.load_puzzle(self.selected_puzzle)
        self.draw_puzzle()
        self.root.ids.help_slider.value = self.ui.puzzle.default_help_level

    def update_help(self, inst=None, value=None):
        if value is None:
            value = self.root.ids.help_slider.value
        if self.ui.puzzle:
            self._help_highlight_devices(value)
            self._help_update_tooltips(value)

    def update_help_highlight_devices(self):
        self._help_highlight_devices(self.root.ids.help_slider.value)

    def update_puzzle_list(self, popup=None):
        # TODO: At the moment self.filter is a list that can include 0 or more
        # puzzle names, but getAllPuzzleNames only accepts a single string. So
        # we currenly just accept the first item in the list as the filter.
        pfilter = None
        if isinstance(self.filters, list) and len(self.filters) > 0:
            pfilter = f"{self.filters[0]}"
        elif isinstance(self.filters, str):
            pfilter = self.filters
        self.filtered_puzzlelist = self.ui.getAllPuzzleNames(pfilter)
        if popup:
            popup.ids.puzzles_view.update_data()

    def update_undo_redo_states(self):
        def set_state(wid, lst):
            disabled = False
            if len(lst) == 0:
                disabled = True
            wid.disabled = disabled

        set_state(self.root.ids.undo, session.undolist)
        set_state(self.root.ids.redo, session.redolist)

    def user_select_device(self):
        # TODO: Add on-screen indicator that a device needs to be selected.
        if not hasattr(self, "chosen_device"):
            self.chosen_device = None
        elif self.chosen_device:
            logging.info(f"GUI: User selected device: {self.chosen_device.hostname}")

    def user_select_nic(self, devicew):
        if not hasattr(self, "chosen_nic"):
            self.chosen_nic = None
            ChooseNicPopup(devicew).open()
        elif self.chosen_nic:
            logging.info(f"GUI: User selected NIC: {self.chosen_nic}")

    def user_select_position(self):
        if not hasattr(self, "chosen_pos"):
            self.chosen_pos = None
        elif self.chosen_pos:
            logging.info(f"GUI: User selected pos: {self.chosen_pos}")

    def _get_widget_by_prop(self, prop, value):
        for w in self.root.ids.layout.children:
            if hasattr(w, prop) and getattr(w, prop) == value:
                return w

    def _get_widgets_by_class_name(self, name):
        widgets = []
        for w in self.root.ids.layout.children:
            if w.__class__.__name__ == name:
                widgets.append(w)
        return widgets

    def _help_highlight_devices(self, help_level=None):
        """
        Always runs when help level is initialized or changed.
        """
        # Skip if no puzzle loaded.
        if not self.ui or not self.ui.puzzle or help_level is None:
            return
        # Clear existing highlights (to be redrawn next).
        # NOTE: Invariant emblems don't get removed.
        for c in self.root.ids.layout.children:
            if isinstance(c, HelpHighlight):
                # print(f"Removing highlight for {c.base.hostname}")
                self.root.ids.layout.remove_widget(c)
        # Add any required highlights.
        if help_level > 0:
            # TODO: This only highlights layout devices. We still need to work
            # in highlighting of other on-screen elements.
            for n, t in (
                (e.get("shost"), e.get("thetest"))
                for e in self.ui.all_tests()
                if not e.get("completed")
            ):
                d = self.ui.get_device(n)
                if d is None:
                    logging.info(f'Ignoring highlight of non-device "{n}"')
                    continue
                w = self.get_widget_by_hostname(n)
                if isinstance(w, Device) and not w.base.is_invisible:
                    match t:
                        case "LockAll":
                            # Ignore. Used for fluorescent light in packet
                            # corruption puzzle.
                            continue
                        case "LockLocation":
                            # Device can't be moved.
                            w.lock()
                        case _:
                            w.highlight()

    def _help_update_tooltips(self, help_level):
        # List devices and help_texts.
        devices = {d.hostname: "" for d in self.devices}
        for test_data in self.ui.all_tests():
            nettest = nettests.NetTest(test_data)
            device = nettest.shost
            help_text = nettest.get_help_text(help_level)
            if not devices.get(device):
                devices[device] = help_text
            else:
                devices[device] += f"\n{help_text}"

        # Apply each device's help_text.
        for device, help_text in devices.items():
            d = self.get_widget_by_hostname(device)
            if hasattr(d, "button"):
                d.update_tooltip_text(help_text)

    def _new_device(self, *args):
        """Create a new device in the puzzle layout.

        This method is called repeatedly until each aspect of the new device is
        defined and the device is created.
        """
        if not hasattr(self, "new_device_data"):
            self.new_device_data = [self._new_device_type]
            del self._new_device_type
            Clock.schedule_once(self._new_device)
        elif len(self.new_device_data) == 1:
            # Set position.
            self.user_select_position()
            if self.chosen_pos:
                # Convert pos to puzzle coords.
                loc = pos_to_location(self.chosen_pos, self.root.ids.layout.size)
                loc_str = ",".join([str(e) for e in loc])
                self.new_device_data.append(loc_str)
                del self.chosen_pos
            Clock.schedule_once(self._new_device)
        else:
            cmd = ["create", "device", *self.new_device_data]
            del self.new_device_data
            self.ui.parse(" ".join(cmd))

    def _new_link(self, *args):
        """Create a new link in the puzzle layout.

        This method is called repeatedly until each aspect of the new link is
        defined and the link is created.
        """
        if not hasattr(self, "new_link_data"):
            self.new_link_data = []
            Clock.schedule_once(self._new_link)
        elif len(self.new_link_data) < 1:
            self.user_select_device()
            if self.chosen_device:
                self.new_link_data.append(self.chosen_device.hostname)
                del self.chosen_device
            Clock.schedule_once(self._new_link)
        elif len(self.new_link_data) < 2:
            srcdev = self.get_widget_by_hostname(self.new_link_data[0])
            self.user_select_nic(srcdev)
            if self.chosen_nic:
                self.new_link_data.append(self.chosen_nic)
                del self.chosen_nic
            Clock.schedule_once(self._new_link)
        elif len(self.new_link_data) < 3:
            self.user_select_device()
            if self.chosen_device:
                self.new_link_data.append(self.chosen_device.hostname)
                del self.chosen_device
            Clock.schedule_once(self._new_link)
        elif len(self.new_link_data) < 4:
            dstdev = self.get_widget_by_hostname(self.new_link_data[2])
            self.user_select_nic(dstdev)
            if self.chosen_nic:
                self.new_link_data.append(self.chosen_nic)
                del self.chosen_nic
            Clock.schedule_once(self._new_link)
        else:
            # Construct the parser command.
            cmd = ["create", "link", *self.new_link_data]
            del self.new_link_data
            self.ui.parse(" ".join(cmd))

    def _print_stats(self, *args):
        # show_grid(self)
        print_layout_info(self)

    def _set_left_panel_width(self, *args):
        menu = self.root.ids.menu
        menu_buttons = menu.children
        self.root.ids.left_panel.width = sum(
            [
                menu_buttons[0].width * len(menu_buttons),
                menu.padding * 2,
                menu.spacing * (len(menu_buttons) - 1),
            ]
        )

    def _update_packets(self, *args):
        # Skip if no puzzle is loaded.
        if not self.ui.puzzle:
            return

        # Update backend packet info.
        self.ui.process_packets(self.packet_progress_rate)

        # Update packets.
        self.packetmgr.update_packets()

        # Update other GUI elements that depend on completed pings.
        self.check_puzzle()
        self.update_help()

    def _test(self, *args, **kwargs):
        # raise NotImplementedError
        for d in self.devices:
            print(f"{d.nics=}")


class PuzzlesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.update_puzzle_list()
        self.selected_item = None
        self.update_data()

    def update_data(self):
        self.data = [{"text": n} for n in self.app.filtered_puzzlelist]
