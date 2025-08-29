import logging
from copy import deepcopy
from kivy.clock import Clock
from kivy.graphics import Color
from kivy.graphics import Ellipse
from kivy.metrics import dp
from kivy.uix.behaviors import DragBehavior
from kivy.uix.gridlayout import GridLayout

from .. import _
from .. import device
from .. import interface
from .. import nic
from .. import session
from .base import AppRecView
from .base import get_layout_height
from .base import HelpHighlight
from .base import hide_widget
from .base import location_to_pos
from .base import LockEmblem
from .base import NETWORK_ITEMS
from .base import pos_to_location
from .buttons import CommandButton
from .buttons import DeviceButton
from .labels import DeviceLabel
from .layouts import ThemedBoxLayout
from .popups import AppPopup


class Device(DragBehavior, ThemedBoxLayout):
    def __init__(self, init_data=None, **kwargs):
        self.base = device.Device(init_data)
        super().__init__(**kwargs)
        self.app = session.app
        self.help_text = None
        self.highlighting = None
        self.lock_icon = None
        self.loc_init = self.base.location
        self._location_locked = False
        # Set final attributes.
        self._set_image()
        self.center = location_to_pos(self.base.location, self.app.root.ids.layout.size)
        # Updates that rely on Device's pos already being set.
        Clock.schedule_once(self.set_power_status)

    @property
    def button(self):
        for c in self.children:
            if c.__class__.__name__ == "DeviceButton":
                return c

    @property
    def hostname(self):
        # NOTE: @properties seem to be evaluated during super(), which is before
        # self.base is defined.
        if hasattr(self, "base") and self.base:
            return self.base.hostname

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
        if hasattr(self, "base") and self.base:
            return [nic.Nic(n) for n in self.base.all_nics()]
        else:
            return list()

    @property
    def uniqueidentifier(self):
        if hasattr(self, "base") and self.base:
            return self.base.uniqueidentifier

    def callback(self, cmd_string):
        self.app.ui.parse(cmd_string)

    def get_nic(self, name):
        for n in self.nics:
            if n.name == name:
                return n

    def highlight(self, do_highlight=True):
        if do_highlight:
            # Add highlight.
            # logging.debug(f"GUI: Add highlight for {self.hostname}")
            if not self.highlighting:
                self.highlighting = HelpHighlight(base=self)
            if self.highlighting not in self.app.root.ids.layout.children:
                # Set draw index one higher than (i.e. behind) Device.
                idx = self.parent.children.index(self) + 1
                self.app.root.ids.layout.add_widget(self.highlighting, idx)
        else:
            # Remove highlight.
            # logging.debug(f"GUI: Remove highlight for {self.hostname}")
            if (
                self.highlighting
                and self.highlighting in self.app.root.ids.layout.children
            ):
                self.app.root.ids.layout.remove_widget(self.highlighting)
            self.highlighting = None

    def hide(self, do_hide=True):
        # Ensure base object state matches GUI object state.
        self.base.is_invisible = do_hide
        if do_hide:
            logging.debug(f"GUI: Hide {self.hostname} & dependent items.")
            # Hide any help highlight.
            self.highlight(False)
        elif do_hide is False:
            logging.debug(f"GUI: Show {self.hostname} & dependent items.")
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

    def on_press(self):
        if hasattr(self.app, "chosen_device"):
            self.app.chosen_device = self
            return True
        self._build_commands_popup().open()

    def set_power_status(self, *args):
        if self.base.powered_on:
            self.canvas.after.clear()
        else:
            pos = (self.button.x + self.button.width - dp(15), self.button.y + dp(5))
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
        commands.extend(self.base.get_nontest_commands())
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
        popup = CommandsPopup(content=content, title=self.base.hostname)
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
        img = devices.get(self.base.json.get("mytype")).get("img")
        if img is None:
            raise TypeError(f"Unhandled device type: {self.base.json.get('mytype')}")
        self.button.background_normal = str(self.app.IMAGES / img)

    def _post_move(self, *args):
        # Show hidden links.
        for lnk in self.links:
            lnk.hide(False)


class CommandsPopup(AppPopup):
    pass


class PingHostPopup(AppPopup):
    def __init__(self, dev, **kwargs):
        self.device = dev
        super().__init__(**kwargs)

    def on_okay(self, dest):
        self.app.ui.parse(f"ping {self.device.hostname} {dest}")
        self.dismiss()


class EditDevicePopup(AppPopup):
    def __init__(self, dev, **kwargs):
        # Use copy of data for displaying in UI b/c real changes will be
        # applied via parser commands when "Okay" is clicked.
        self.device = Device(deepcopy(dev.base.json))
        super().__init__(**kwargs)
        self.selected_ip = None
        self.selected_nic = None
        self.puzzle_commands = list()

    def on_gateway(self):
        raise NotImplementedError

    def on_routes(self):
        raise NotImplementedError

    def on_vlans(self):
        raise NotImplementedError

    def on_nics_edit(self):
        raise NotImplementedError

    def on_nic_selection(self, selected_nic):
        self.selected_ip = None
        self.root.ids.edit_ip.disabled = True
        self.root.ids.remove_ip.disabled = True
        self.selected_nic = selected_nic
        self.root.ids.edit_nic.disabled = False
        self.root.ids.add_ip.disabled = False
        self._set_ips()

    def on_ips_add(self):
        # Send correct NIC and interface data to IP Popup.
        n = self.device.get_nic(self.selected_nic)
        ip_config = self._get_ip_config_from_nic(n, n.name)
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

    def on_ips_edit(self):
        if not self.selected_ip:
            logging.warning("GUI: No IP selected for editing.")
            return
        ip_config = self._get_ip_config_from_nic(
            self.device.get_nic(self.selected_nic), self.selected_ip
        )
        if ip_config:
            EditIpPopup(self, ip_config).open()

    def on_ip_selection(self, selected_ip):
        self.selected_ip = selected_ip
        self.root.ids.remove_ip.disabled = False
        self.root.ids.edit_ip.disabled = False

    def on_cancel(self):
        self.dismiss()

    def on_okay(self):
        logging.info(f"GUI: Updating {self.device.hostname}:")
        for cmd in self.puzzle_commands:
            logging.info(f"GUI: > {cmd}")
            self.app.ui.parse(cmd)
        # Update GUI helps b/c it will trigger tooltip updates, which are needed
        # b/c IP data has likely changed.
        self.app.update_help()
        self.dismiss()

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
        ips = list()
        n = self.device.get_nic(self.selected_nic)
        logging.debug(f"GUI: {n.name} ifaces: {n.interfaces}")
        for iface_data in n.interfaces:
            iface = interface.Interface(iface_data)
            if iface.nicname == n.name:
                ip_addr = interface.IpAddress(iface.ip_data)
                if not ip_addr.address.startswith("0"):
                    ips.append(iface.ip_data)
                break
        logging.debug(f"GUI: IPs for {self.device.hostname}: {ips}")
        self.ids.ips_list.update_data(ips)


class NICsRecView(AppRecView):
    def update_data(self, nics, management=True):
        self.data = [{"text": n.name} for n in nics if not n.name.startswith("lo")]
        item = {"text": "management_interface0"}
        if not management and item in self.data:
            self.data.remove(item)

    def on_selection(self, index):
        self.root.on_nic_selection(self.data[index].get("text"))


class IPsRecView(AppRecView):
    def update_data(self, ips):
        self.data = [{"text": f"{d.get('ip')}/{d.get('mask')}"} for d in ips]

    def on_selection(self, index):
        self.root.on_ip_selection(self.data[index].get("text"))


class EditIpPopup(AppPopup):
    def __init__(self, device_popup, ip_address, **kwargs):
        self.device_popup = device_popup
        self.ip_address = ip_address
        super().__init__(**kwargs)

    def on_cancel(self):
        self.dismiss()

    def on_okay(self):
        # Update IPs in IPs list.
        self.device_popup._set_ips()
        # self.device_popup.device.update_tooltip_text()
        # Add updating command.
        self.device_popup.puzzle_commands.append(
            f"set {self.device_popup.device.hostname} {self.device_popup.selected_nic} {self.ip_address.address}/{self.ip_address.netmask}"
        )
        self.dismiss()

    def set_address(self, input_inst):
        if not input_inst.focus:
            self.ip_address.address = input_inst.text

    def set_netmask(self, input_inst):
        if not input_inst.focus:
            self.ip_address.netmask = input_inst.text

    def set_gateway(self, input_inst):
        if not input_inst.focus:
            self.ip_address.gateway = input_inst.text


class ChooseNicPopup(AppPopup):
    def __init__(self, devicew, **kwargs):
        self.device = devicew
        super().__init__(**kwargs)
        self.selected_nic = None
        free_nics = [
            n for n in self.device.nics if device.linkConnectedToNic(n.json) is None
        ]
        self.ids.nics_list.update_data(free_nics, management=False)

    def on_nic_selection(self, selected_nic):
        self.selected_nic = selected_nic

    def on_okay(self):
        self.app.chosen_nic = self.selected_nic
        self.dismiss()
