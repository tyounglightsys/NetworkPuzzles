import logging

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.relativelayout import RelativeLayout

from .. import _, session
from .base import NETWORK_ITEMS, pos_to_location
from .buttons import MenuButton


class ThemedBoxLayout(BoxLayout):
    pass


class SingleRowLayout(ThemedBoxLayout):
    pass


class ActionPopupButtons(SingleRowLayout):
    cancel_text = StringProperty(f"{_('Cancel')}")
    okay_text = StringProperty(f"{_('Okay')}")

    # Register custom events to be passed onto root popup, etc.
    # ref: https://stackoverflow.com/questions/65551226/kivy-reusing-a-toggle-button-layout-but-assigning-different-functions-to-the-b/66181173#66181173
    def __init__(self, **kwargs):
        self.register_event_type("on_cancel")
        self.register_event_type("on_okay")
        super().__init__(**kwargs)

    def cancel(self):
        # self.on_cancel()
        self.dispatch("on_cancel")

    def okay(self):
        # self.on_okay()
        self.dispatch("on_okay")

    def on_cancel(self):
        pass

    def on_okay(self):
        pass


class AppTray(ThemedBoxLayout):
    def __init__(
        self, choices=list(), orientation="horizontal", parent_button=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.parent_button = parent_button
        self.choices = choices
        self.buttons = [MenuButton(c) for c in self.choices]
        self.orientation = orientation

    @property
    def app(self):
        return session.app

    @property
    def is_open(self):
        return len(self.children) > 0

    def close(self):
        self.clear_widgets()
        self.app.root.ids.layout.remove_widget(self)

    def open(self):
        self.app.root.ids.layout.add_widget(self)
        for b in self.buttons:
            self.add_widget(b)
        self._set_size()
        self._set_pos()

    def _set_pos(self):
        if self.orientation == "horizontal":
            # NOTE: The tray's pos is immediately adjacent to the anchor button.
            x = self.parent_button.pos[0] + self.height
            y = self.parent_button.pos[1]
        else:
            # NOTE: The tray's pos is offset down from the anchor button by the
            # tray's height.
            x = self.parent_button.pos[0]
            y = self.parent_button.pos[1] - self.height
        self.pos = (x, y)

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def _set_size(self):
        length = len(self.children)
        breadth = self.app.BUTTON_MAX_H + dp(10)  # 10px more for padding
        if self.orientation == "horizontal":
            self.width = length * breadth
            self.height = breadth
        else:
            self.width = breadth
            self.height = length * breadth


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """Adds selection and focus behaviour to the view."""

    pass


class PuzzleLayout(RelativeLayout):
    terminal_font_size = NumericProperty(sp(12))
    terminal_line_height = NumericProperty(sp(12 + 4))
    terminal_lines = NumericProperty(7)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.items_menu_button = MenuButton(
            props={"text": "+", "cb": self.on_new_item, "info": "add new item"},
            pos_hint={"x": 0.005, "top": 0.99},
        )

        # Define button trays.
        self.items_tray = AppTray(
            parent_button=self.items_menu_button,
            choices=self._get_items_choices(),
            orientation="vertical",
        )
        self.infra_devices_tray = AppTray(
            parent_button=self.items_tray.buttons[1],
            choices=self._get_infra_devices_choices(),
        )
        self.user_devices_tray = AppTray(
            parent_button=self.items_tray.buttons[2],
            choices=self._get_user_devices_choices(),
        )

    @property
    def app(self):
        return session.app

    @property
    def devices(self):
        return self._get_widgets_by_class_name("GuiDevice")

    @property
    def links(self):
        return self._get_widgets_by_class_name("GuiLink")

    @property
    def packets(self):
        return self._get_widgets_by_class_name("GuiPacket")

    def add_device(self, devicew, devicetype=None):
        # Handle creation of new link.
        if isinstance(devicew, MenuButton):
            self._add_item(data=devicew, itemtype="device", devicetype=devicetype)
            return

        # Hide invisible devices.
        if devicew.is_invisible:
            devicew.hide()

        # Add device to layout.
        self.add_widget(devicew)

    def _add_item(self, data=None, itemtype=None, devicetype=None):
        # Import here to avoid circular imports.
        from .devices import GuiDevice
        from .links import GuiLink

        if isinstance(data, dict):
            if itemtype == "device":
                data = GuiDevice(json_data=data)
            elif itemtype == "link":
                data = GuiLink(json_data=data)
        if isinstance(data, GuiDevice):
            self.add_device(data)
            return
        elif isinstance(data, GuiLink):
            self.add_link(data)
            return
        # Ensure new item menus are closed.
        self.close_trays()

        if isinstance(data, MenuButton):
            if itemtype == "device":
                # Initiate new device creation sequence.
                self._new_device_type = devicetype
                Clock.schedule_once(self._new_device)
            elif itemtype == "link":
                # Initiate new link creation sequence.
                Clock.schedule_once(self._new_link)

    def add_items_menu_button(self):
        self.add_widget(self.items_menu_button)

    def add_link(self, linkw=None):
        # Handle creation of new link.
        if isinstance(linkw, MenuButton):
            self._add_item(data=linkw, itemtype="link")
            return

        # Hide links connected to invisible devices.
        for host in (linkw.src, linkw.dest):
            w = self.get_widget_by_hostname(host)
            if w.is_invisible:
                linkw.hide()

        # Add link to z-index = 99 to ensure it's drawn under devices.
        self.add_widget(linkw, 99)

    def close_trays(self):
        # Close tray and subtrays if open.
        for tray in (
            self.infra_devices_tray,
            self.user_devices_tray,
            self.items_tray,
        ):
            tray.close()

    def draw_devices(self, devices):
        from .devices import GuiDevice  # avoid circular import

        for d in devices:
            self.add_device(GuiDevice(json_data=d))

    def draw_links(self, links):
        from .links import GuiLink  # avoid circular import

        for d in links:
            self.add_link(GuiLink(json_data=d))

    def get_first_link_index(self):
        first_index = None
        for w in self.links:
            idx = self.children.index(w)
            if first_index is None:
                first_index = idx
            else:
                first_index = min((idx, first_index))
        return first_index

    def get_widget_by_hostname(self, hostname):
        return self._get_widget_by_prop("hostname", hostname)

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
                loc = pos_to_location(self.chosen_pos, self.size)
                loc_str = ",".join([str(e) for e in loc])
                self.new_device_data.append(loc_str)
                del self.chosen_pos
            Clock.schedule_once(self._new_device)
        else:
            cmd = ["create", "device", *self.new_device_data]
            del self.new_device_data
            self.app.ui.parse(" ".join(cmd))

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
            self.app.ui.parse(" ".join(cmd))

    def on_new_infra_device(self, inst):
        self.infra_devices_tray.toggle()

    def on_new_item(self, inst):
        self.items_tray.toggle()

    def on_new_user_device(self, inst):
        self.user_devices_tray.toggle()

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if touch.button == "left" or touch.button is None:
                if hasattr(self, "chosen_pos"):
                    # NOTE: If touch.grab_list is populated it means that a
                    # widget was touched instead of empty space. Do not set the
                    # chosen_pos, wait instead for another touch. Either way, True
                    # should be returned so that the touch is not propagated.
                    if len(touch.grab_list) == 0:
                        self.chosen_pos = self.to_widget(*touch.pos)
                    return True
                # NOTE: The touch has to be explicitly passed on so that child
                # widgets can receive it; e.g. so that Device buttons are able
                # to be "pressed".
                return super().on_touch_up(touch)

    def remove_item(self, item):
        """Remove widget from layout by widget or item JSON data."""
        # Import here to avoid circular imports.
        from .devices import GuiDevice
        from .links import GuiLink

        # TODO: Add parser command to also remove widget from puzzle JSON.
        widget = None
        if isinstance(item, GuiLink) or isinstance(item, GuiDevice):
            widget = item
        elif isinstance(item, dict):
            widget = self.get_widget_by_hostname(item.get("hostname"))
        else:
            raise TypeError(f"{type(item)=}")
        if widget:
            self.remove_widget(widget)

    def reset(self):
        # Remove any remaining child widgets from puzzle layout.
        self.clear_widgets()
        # Redraw the "+" button for adding new items.
        self.add_items_menu_button()

    def reset_vars(self):
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

    def show_devices_with_open_ports(self):
        logging.debug(f"TEST: {self.devices=}")

    def user_select_device(self):
        # TODO: Add on-screen indicator that a device needs to be selected.
        if not hasattr(self, "chosen_device"):
            self.chosen_device = None
        elif self.chosen_device:
            logging.info(
                f"layouts: User selected device: {self.chosen_device.hostname}"
            )

    def user_select_nic(self, devicew):
        if not hasattr(self, "chosen_nic"):
            self.chosen_nic = None
            # Import popup here to avoid circular imports.
            from .popups import ChooseNicPopup

            ChooseNicPopup(device=devicew).open()
        elif self.chosen_nic:
            logging.info(f"layouts: User selected NIC: {self.chosen_nic}")

    def user_select_position(self):
        if not hasattr(self, "chosen_pos"):
            self.chosen_pos = None
        elif self.chosen_pos:
            logging.info(f"layouts: User selected pos: {self.chosen_pos}")

    def _get_infra_devices_choices(self):
        choices = []
        for dtype, choice in NETWORK_ITEMS.get("devices").get("infrastructure").items():
            choice["cb"] = self.add_device
            choice["cb_kwargs"] = {"devicetype": dtype}
            choice["orientation"] = "horizontal"
            choices.append(choice)
        return choices

    def _get_items_choices(self):
        return [
            {"img": "link.png", "cb": self.add_link, "info": "add link"},
            {
                "img": "Switch.png",
                "cb": self.on_new_infra_device,
                "info": "infrastructure devices",
            },
            {
                "img": "PC.png",
                "cb": self.on_new_user_device,
                "info": "user devices",
            },
        ]

    def _get_user_devices_choices(self):
        choices = []
        for dtype, choice in NETWORK_ITEMS.get("devices").get("user").items():
            choice["cb"] = self.add_device
            choice["cb_kwargs"] = {"devicetype": dtype}
            choice["orientation"] = "horizontal"
            choices.append(choice)
        return choices

    def _get_widget_by_prop(self, prop, value):
        for w in self.children:
            if hasattr(w, prop) and getattr(w, prop) == value:
                return w

    def _get_widgets_by_class_name(self, name):
        widgets = []
        for w in self.children:
            if w.__class__.__name__ == name:
                widgets.append(w)
        return widgets
