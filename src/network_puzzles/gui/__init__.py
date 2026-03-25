import logging
import traceback

# Remove root logger b/c kivy's logger will handle all logging.
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    root_logger.removeHandler(handler)

from kivy.config import Config

from .. import session

if session.device_type == "desktop":
    # Disable right-click red dot.
    Config.set("input", "mouse", "mouse,disable_multitouch")
elif session.device_type == "mobile":
    Config.set("kivy", "desktop", "0")

# Continue with remaining imports.
from kivy.app import App
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.textinput import TextInput

from .. import messages, nettests
from ..puzzle import PuzzleTest
from .base import (
    BUTTON_FONT_SIZE,
    BUTTON_MAX_H,
    DEVICE_BUTTON_MAX_H,
    IMAGES_DIR,
    PACKET_DIMS,
    HelpHighlight,
    LightColorTheme,
    print_layout_info,
    show_grid,
)
from .devices import GuiDevice
from .packets import PacketManager
from .popups import (
    CommandPopup,
    ExceptionPopup,
    PuzzleChooserPopup,
    PuzzleCompletePopup,
)


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
            # Force orientation to landscape.
            Window.orientation = 0
            # Force loglevel to DEBUG.
            logger = logging.getLogger()
            logger.level = logging.DEBUG
            self.packet_tick_delay = 0.04  # packet pos refresh rate in seconds
            self.packet_progress_rate = 6  # % of link traveled each tick
        logging.debug(f"App: {session.device_type=}")

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

        # Log config details.
        for sect, data in Config._sections.items():
            logging.debug(f"Config: {sect}:")
            for k, v in data.items():
                logging.debug(f"Config:  {k} = {v}")

    def check_puzzle(self, *args):
        """Checked at regular interval during kivy app loop."""
        if self.ui.update_puzzle_completion_status():
            PuzzleCompletePopup().open()

    def add_terminal_line(self, line):
        if not line.endswith("\n"):
            line += "\n"
        self.root.ids.terminal.text += f"{self.ui.PS1} {line}"

    def draw_links(self, *args):
        self.root.ids.layout.draw_links(
            d for d in self.ui.puzzle.links if d is not None
        )
        self._print_stats()

    def draw_puzzle(self, *args):
        """Clear puzzle layout area; draw all elements related to current puzzle."""
        # logging.debug(
        #     f"App: {self.root.ids.layout.__class__.__name__}: pos={self.root.ids.layout.pos}; size={self.root.ids.layout.size}"
        # )
        if not self.ui.puzzle:
            logging.warning("GUI: No puzzle is loaded.")
            return

        self.reset_display()

        # Get puzzle text from localized messages, if possible, but fallback to
        # English text in JSON data.
        puzzle_data = self.ui.puzzle.json
        logging.debug(f"App: {self.ui.puzzle.uid=}")
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
        self.root.ids.layout.draw_devices(self.ui.puzzle.devices)

        # Some setup needs to be done one tick after devices, because their
        # positions depend on the devices' positions.
        Clock.schedule_once(self.update_help)
        Clock.schedule_once(self.draw_links)

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

    def reset_display(self):
        """Clear display without clearing loaded puzzle data."""
        # Reset the layout area.
        self.root.ids.layout.reset()
        self.title = self.app_title
        logging.debug(f"App: window size: {Window.size}")
        # logging.debug(f"App: puzzle layout width: {self.root.ids.layout.width}")
        logging.debug(f"App: layout height: {self.root.ids.layout.height}")
        logging.debug(f"App: terminal height: {self.root.ids.terminal.height}")

    def reset_vars(self):
        # Set variables to intial values.
        self.filtered_puzzles = []
        self.filters = []
        if self.root:
            # Delete temporary variables.
            self.root.ids.layout.reset_vars()

    def setup_puzzle(self, *args):
        self.reset_vars()
        self.ui.load_puzzle(self.selected_puzzle)
        self.draw_puzzle()
        self.root.ids.help_slider.value = self.ui.puzzle.default_help_level

    def update_help(self, inst=None, value=None):
        if self.ui.puzzle:
            if value is None:
                value = self.root.ids.help_slider.value
            self._help_highlight_devices(value)
            self._help_update_tooltips(value)

    def update_help_highlight_devices(self):
        self._help_highlight_devices(self.root.ids.help_slider.value)

    def update_puzzle_list(self, popup=None):
        pfilter = None
        if isinstance(self.filters, list) and len(self.filters) > 0:
            # Create OR regex string with all filter items.
            pfilter = f"({'|'.join(self.filters)})"
        elif isinstance(self.filters, str):
            # Use filter string directly.
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
                # print(f"Removing highlight for {c.hostname}")
                self.root.ids.layout.remove_widget(c)
        # Add any required highlights.
        if help_level > 0:
            # FIXME: This only highlights layout devices. We still need to work
            # in highlighting of other on-screen elements.
            uncompleted_tests = []
            for test_data in self.ui.all_tests():
                test = PuzzleTest(test_data)
                if not test.completed:
                    uncompleted_tests.append(test)

            for n, t in ((test.shost, test.name) for test in uncompleted_tests):
                d = self.ui.get_device(n)
                if d is None:
                    # logging.info(f'App: Ignoring highlight of non-device "{n}"')
                    continue
                w = self.root.ids.layout.get_widget_by_hostname(n)
                if isinstance(w, GuiDevice) and not w.is_invisible:
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
        devs = {d.hostname: "" for d in self.root.ids.layout.devices}
        for test_data in self.ui.all_tests():
            nettest = nettests.NetTest(test_data)
            dev = nettest.shost
            help_text = nettest.get_help_text(help_level)
            if not devs.get(dev):
                devs[dev] = help_text
            else:
                devs[dev] += f"\n{help_text}"

        # Apply each device's help_text.
        for dev, help_text in devs.items():
            d = self.root.ids.layout.get_widget_by_hostname(dev)
            if hasattr(d, "button"):
                d.update_tooltip_text(help_text)

    def _print_stats(self, *args, grid=False):
        if grid:
            show_grid(self)
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
        raise NotImplementedError


class TerminalLabel(TextInput):
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):  # touch outside of Terminal
            # Cancel any text selection.
            self.cancel_selection()
            # Hide the Cut/Copy/Paste bubble.
            self._hide_cut_copy_paste()
            # Hide the selection handles.
            self._hide_handles()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        # Open popup on right-click within the Terminal area (only works on
        # desktop devices, where touch.button is not None).
        # REF: https://kivy.org/doc/master/guide/inputs.html#grabbing-touch-events
        if touch.button == "right" and touch.grab_current is self:
            touch.ungrab(self)
            CommandPopup().open()
            return True


class AppExceptionHandler(ExceptionHandler):
    def handle_exception(self, exception):
        ExceptionPopup(message=traceback.format_exc()).open()
        # return ExceptionManager.RAISE  # kills app right away
        return ExceptionManager.PASS
