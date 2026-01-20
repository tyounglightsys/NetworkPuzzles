import logging
from copy import deepcopy

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.behaviors import DragBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from .. import _, interface, nic, session
from ..device import Device
from .base import (
    NETWORK_ITEMS,
    HelpHighlight,
    LockEmblem,
    ThemedCheckBox,
    get_layout_height,
    hide_widget,
    location_to_pos,
    pos_to_location,
)
from .buttons import CommandButton, ThemedButton
from .labels import CheckBoxLabel
from .layouts import SingleRowLayout, ThemedBoxLayout
from .popups import (
    ActionPopup,
    ChooseNicPopup,  # noqa: F401
    DeviceCommandsPopup,
    EditDhcpPopup,
    EditIpPopup,
    PingHostPopup,
)


class GuiDevice(DragBehavior, ThemedBoxLayout, Device):
    def __init__(self, json_data, **kwargs):
        super().__init__(json_data=json_data, **kwargs)
        self.help_text = None
        self.highlighting = None
        self.lock_icon = None
        self.loc_init = self.location
        self._location_locked = False
        # Set final attributes.
        self._set_image()
        self.center = location_to_pos(self.location, self.app.root.ids.layout.size)
        # Updates that rely on Device's pos already being set.
        Clock.schedule_once(self.set_power_status)

    @property
    def app(self):
        return session.app

    @property
    def button(self):
        for c in self.children:
            if c.__class__.__name__ == "DeviceButton":
                return c

    @property
    def links(self):
        links = list()
        for lnk in self.app.links:
            if self.hostname in lnk.hostname:
                links.append(lnk)
        return links

    @property
    def location_locked(self):
        return self._location_locked

    @location_locked.setter
    def location_locked(self, value):
        if not isinstance(value, bool):
            raise ValueError("Value must be a boolean.")
        self._location_locked = value

    @property
    def nics(self):
        return [nic.Nic(n) for n in self.all_nics()]

    def callback(self, cmd_string):
        self.app.ui.parse(cmd_string)

    def get_height(self):
        h = self.padding[1] + self.padding[3]
        for i, c in enumerate(self.children):
            if i > 0:
                h += self.spacing
            h += c.height
        return h

    def get_nic(self, name):
        for n in self.nics:
            if n.name == name:
                return n

    def highlight(self, do_highlight=True):
        if do_highlight:
            # Add highlight.
            # logging.debug(f"Devices: Add highlight for {self.hostname}")
            if not self.highlighting:
                self.highlighting = HelpHighlight(base=self)
            if self.highlighting not in self.app.root.ids.layout.children:
                # Set draw index one higher than (i.e. behind) Device.
                idx = self.parent.children.index(self) + 1
                self.app.root.ids.layout.add_widget(self.highlighting, idx)
        else:
            # Remove highlight.
            # logging.debug(f"Devices: Remove highlight for {self.hostname}")
            if (
                self.highlighting
                and self.highlighting in self.app.root.ids.layout.children
            ):
                self.app.root.ids.layout.remove_widget(self.highlighting)
            self.highlighting = None

    def hide(self, do_hide=True):
        # Ensure base object state matches GUI object state.
        self.is_invisible = do_hide
        if do_hide:
            logging.debug(f"Devices: Hide {self.hostname} & dependent items.")
            # Hide any help highlight.
            self.highlight(False)
        elif do_hide is False:
            logging.debug(f"Devices: Show {self.hostname} & dependent items.")
            # Show help highlight if relevant.
            self.app.update_help_highlight_devices()
        # Hide/show any links.
        for lnk in self.links:
            lnk.hide(do_hide)
        # Hide/show self.
        hide_widget(self, do_hide)

    def lock(self, activate=True):
        if self.location_locked != activate:
            # Locked state has changed; update device.
            self.location_locked = activate
            if self.location_locked:
                drag_size = (0, 0)
                self.lock_icon = LockEmblem(self)
                self.app.root.ids.layout.add_widget(self.lock_icon)
            else:
                drag_size = (self.width, self.height)
                self.app.root.ids.layout.remove_widget(self.lock_icon)
                self.lock_icon = None
            self.drag_rectangle = (*self.drag_rectangle[:2], *drag_size)

    def move(self, loc):
        # Show if hidden.
        if self.opacity == 0:
            self.hide(False)
        # Move device in JSON data.
        self.app.ui.parse(f"set {self.hostname} pos {loc[0]} {loc[1]}")
        Clock.schedule_once(self._post_move)

    def on_pos(self, *args):
        if 0 in self.pos or self.location_locked:
            # Ignore pos change until device widget is fully placed.
            return True
        loc = pos_to_location(self.center, self.app.root.ids.layout.size)
        if loc != self.loc_init:
            self.move(loc)

    def on_release(self):
        if hasattr(self.app, "chosen_device"):
            self.app.chosen_device = self
            return
        self._build_commands_popup().open()

    def set_power_status(self, *args):
        if self.powered_on:
            self.canvas.after.clear()
        else:
            if self.blown_up:
                smoke = Image(
                    source=str(self.app.IMAGES / "BurnMark.png"),
                    allow_stretch=True,
                    keep_ratio=False,
                    size=(self.button.width, self.button.height / 2),
                    center=self.button.center,
                )
                self.button.add_widget(smoke)
                factor = 2
                w = self.button.width * factor
                h = self.button.height * factor
                x = self.button.center_x - (w / 2)
                y = self.button.center_y
                gif = Image(
                    source=str(self.app.IMAGES / "animations" / "explosion.zip"),
                    anim_delay=150 / 1000,
                    anim_loop=1,
                    size=(w, h),
                    pos=(x, y),
                )
                self.button.add_widget(gif)
            else:
                pos = (
                    self.button.x + self.button.width - dp(15),
                    self.button.y + dp(5),
                )
                with self.canvas.after:
                    Color(rgb=(1, 0, 0))
                    Ellipse(pos=pos, size=(dp(8), dp(8)))

    def update_tooltip_text(self, help_text=None):
        info = self._extra_tooltip_text()
        if help_text:
            self.help_text = help_text
        if self.help_text:
            info += f"\n{self.help_text}"
        self.button.info = info

    def _build_commands_popup(self):
        # Build commands list (might change if state changes).
        commands = [_("Ping [host]")]
        commands.extend(session.puzzle.commands_from_tests(self.hostname))
        commands.extend(self.get_nontest_commands())
        commands.append(_("Edit"))

        # Setup the content.
        content = GridLayout(cols=1, spacing=dp(5))
        for command in commands:
            if command == _("Ping [host]"):
                cb = PingHostPopup(
                    self, title=f"{_('Ping [host] from')} {self.hostname}"
                ).open
            elif command == _("Edit"):
                cb = self._edit_device
            else:
                cb = self.callback
            content.add_widget(CommandButton(cb, command))
        content.size_hint_y = None
        content.height = get_layout_height(content)
        # Setup the Popup.
        popup = DeviceCommandsPopup(content=content, title=self.hostname)
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

    def _extra_tooltip_text(self):
        # Add hostname.
        text = self.hostname
        # Add IP addresses and netmasks.
        for n in self.nics:
            for iface in n.interfaces:
                ip = iface.get("myip", {})
                ipaddr = ip.get("ip", "0.0.0.0")
                if ipaddr != "0.0.0.0":
                    text += f"\n{ipaddr}/{ip.get('mask')}"
        return text

    def _edit_device(self, *args):
        EditDevicePopup(title=f"{_('Edit')} {self.hostname}", dev=self).open()

    def _set_image(self):
        devices = NETWORK_ITEMS.get("devices").get("user") | NETWORK_ITEMS.get(
            "devices"
        ).get("infrastructure")
        img = devices.get(self.mytype).get("img")
        if img is None:
            raise TypeError(f"Unhandled device type: {self.mytype}")
        self.button.background_normal = str(self.app.IMAGES / img)

    def _post_move(self, *args):
        # Show hidden links.
        for lnk in self.links:
            lnk.hide(False)


class EditDevicePopup(ActionPopup):
    # TODO: Decide which changes should be made immediately and which ones
    # should only be made when clicking "Okay". Consider: add/remove NICs,
    # add/remove IPs, enable/disable DHCP/firewall, configure DHCP/firewall. One
    # idea is on "Cancel" an equal number of "redo" functions is run that
    # correspond to the number of commands run since the Popup was opened.

    def __init__(self, dev, **kwargs):
        # Use copy of data for displaying in UI b/c real changes will be
        # applied via parser commands when "Okay" is clicked.
        self.device = GuiDevice(json_data=deepcopy(dev.json))
        super().__init__(**kwargs)
        self.selected_ip = None
        self._selected_nic = None
        self.puzzle_commands = list()
        self.dhcp_checkbox = None
        self._add_conditional_widgets()

    @property
    def selected_nic(self):
        return self._selected_nic

    @selected_nic.setter
    def selected_nic(self, value):
        # Remove "connected" character & MAC address from displayed value.
        self._selected_nic = value.replace("*", ";").split(";")[0]

    def on_dhcp_button(self):
        EditDhcpPopup(self.device).open()

    def on_dhcp_chkbox(self):
        if self.dhcp_checkbox.state == "normal":  # unchecked
            self.device.is_dhcp = False
        elif self.dhcp_checkbox.state == "down":  # checked
            self.device.is_dhcp = True

    def on_gateway(self):
        if not self.ids.gateway.focus:
            self.puzzle_commands.append(
                f"set {self.device.hostname} gateway {self.ids.gateway.text}"
            )

    def on_routes(self):
        raise NotImplementedError

    def on_vlans(self):
        raise NotImplementedError

    def on_ip_selection(self, selected_ip):
        self.selected_ip = selected_ip
        self.root.ids.remove_ip.disabled = False
        self.root.ids.edit_ip.disabled = False

    def on_ips_add(self):
        # Send correct NIC and interface data to IP Popup.
        n = self.device.get_nic(self.selected_nic)
        ip_config = self._get_ip_config_from_nic(n, n.name)
        if ip_config:
            EditIpPopup(self, ip_config).open()

    def on_ips_edit(self):
        if not self.selected_ip:
            logging.warning("Devices: No IP selected for editing.")
            return
        ip_config = self._get_ip_config_from_nic(
            self.device.get_nic(self.selected_nic), self.selected_ip
        )
        if ip_config:
            EditIpPopup(self, ip_config).open()

    def on_ips_remove(self):
        n = self.device.get_nic(self.selected_nic)
        ip_config = self._get_ip_config_from_nic(n, self.selected_ip)
        if ip_config:
            ip_config.address = "0.0.0.0"
            ip_config.netmask = "0.0.0.0"
            ip_config.gateway = "0.0.0.0"
            # Update IPs in IPs list.
            self._set_ips()
            # Add command to be applied.
            self.puzzle_commands.append(
                f"set {self.device.hostname} {self.selected_nic} {ip_config.address}/{ip_config.netmask}"
            )

    def on_nic_selection(self, selected_nic_text):
        self.selected_ip = None
        self.selected_nic = selected_nic_text
        self.root.ids.add_ip.disabled = False
        self.root.ids.edit_ip.disabled = True
        self.root.ids.remove_ip.disabled = True
        self.root.ids.edit_nic.disabled = False
        self.root.ids.remove_nic.disabled = False
        self._set_ips()

    def on_nics_add(self):
        raise NotImplementedError
        # # Add command to be applied.
        # self.puzzle_commands.append(
        #     f"create {self.device.hostname} {self.selected_nic}"
        # )

    def on_nics_edit(self):
        raise NotImplementedError

    def on_nics_replace(self):
        # De-select label.
        for c in self.ids.nics_list.children[0].children:
            if c.text.startswith(self.selected_nic):
                c.selected = False
                break
        # Replace NIC.
        self.app.ui.parse(f"replace {self.device.hostname} {self.selected_nic}")
        # Update device with new data.
        self.device = GuiDevice(
            json_data=deepcopy(self.app.ui.get_device(self.device.hostname))
        )
        # Update NIC list.
        self.ids.nics_list.update_data(self.device.nics, management=True)

    def on_okay(self):
        logging.info(f"Devices: Updating {self.device.hostname}:")
        for cmd in self.puzzle_commands:
            logging.info(f"Devices: > {cmd}")
            self.app.ui.parse(cmd)
        # Update GUI helps b/c it will trigger tooltip updates, which are needed
        # b/c IP data has likely changed.
        self.app.update_help()
        super().on_okay()

    def _add_conditional_widgets(self):
        if self.device.mytype in ["server"]:
            # Handle DHCP checkbox, label, and button.
            l_cb = SingleRowLayout(
                padding=0,
            )
            if self.device.is_dhcp:
                state = "down"
            else:
                state = "normal"
            self.dhcp_checkbox = DHCPCheckBox(size_hint_x=0.1, state=state)
            t = CheckBoxLabel(text=f"{_('DHCP Server')}", size_hint_x=0.4)
            b = ThemedButton(text=f"{_('Edit DHCP')}", on_release=self.on_dhcp_button)
            for w in [self.dhcp_checkbox, t, b]:
                l_cb.add_widget(w)
            self.root.ids.left_panel.add_widget(l_cb)
        if self.device.mytype in ["router", "switch"]:
            # Handle VLANs button.
            b = ThemedButton(text=f"{_('VLANs')}", on_release=self.on_vlans)
            self.root.ids.left_panel.add_widget(b)
        # Add empty widget at end to push all other widgets to the top.
        self.root.ids.left_panel.add_widget(Widget())

    def _get_ip_config_from_nic(self, nic_obj, value):
        """Return IP config object from NIC.
        Value to search can be NIC name or IP config data.
        """
        ip_config = None
        for iface_data in nic_obj.interfaces:
            iface = interface.Interface(iface_data)
            iface_ip_config = interface.IpAddress(iface.ip_data)
            if self._is_ip_and_gateway(value):
                if value.split("/") == [
                    iface_ip_config.address,
                    iface_ip_config.netmask,
                ]:
                    ip_config = iface_ip_config
                    break
            else:
                if iface.nicname == nic_obj.name:
                    ip_config = iface_ip_config
                    break
        return ip_config

    def _is_ip_and_gateway(self, value):
        return "/" in value

    def _set_ips(self):
        n = self.device.get_nic(self.selected_nic)
        logging.debug(f"Devices: {n.name} ifaces: {n.interfaces}")
        self.ids.ips_list.update_data(n.ip_addresses)


class DHCPCheckBox(ThemedCheckBox):
    @property
    def popup(self):
        w = self
        while w:
            if hasattr(w.parent, "on_dhcp_chkbox"):
                return w.parent
            w = w.parent

    def on_activate(self):
        if self.popup:
            self.popup.on_dhcp_chkbox()
