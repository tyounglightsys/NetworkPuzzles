import logging
from kivy.clock import Clock
from kivy.graphics import Color
from kivy.graphics import Ellipse
from kivy.metrics import dp
from kivy.uix.behaviors import DragBehavior
from kivy.uix.gridlayout import GridLayout

from .. import _
from .. import device
from .. import nic
from .. import session
from .base import AppRecView
from .base import get_layout_height
from .base import HelpHighlight
from .base import hide_widget
from .base import location_to_rel_pos
from .base import NETWORK_ITEMS
from .buttons import CommandButton
from .layouts import ThemedBoxLayout
from .popups import AppPopup


class Device(DragBehavior, ThemedBoxLayout):
    def __init__(self, init_data=None, **kwargs):
        self.base = device.Device(init_data)
        super().__init__(**kwargs)
        self.app = session.app
        self.pos_init = (0, 0)
        self._set_pos()  # sets self.pos_hint
        self._set_image()
        # Updates that rely on Device's pos already being set.
        Clock.schedule_once(self.set_power_status)

    @property
    def button(self):
        for child in self.children:
            if child.__class__.__name__ == "DeviceButton":
                return child
        return None

    @property
    def hostname(self):
        # NOTE: @properties seem to be evaluated during super(), which is before
        # self.base is defined.
        if hasattr(self, "base") and self.base:
            return self.base.hostname

    @property
    def label(self):
        for child in self.children:
            if child.__class__.__name__ == "DeviceLabel":
                return child
        return None

    @property
    def links(self):
        links = list()
        for lnk in self.app.links:
            if self.hostname in lnk.hostname:
                links.append(lnk)
        return links

    @property
    def nics(self):
        if hasattr(self, "base") and self.base:
            return [nic.Nic(n) for n in self.base.all_nics()]
        else:
            return list()

    @property
    def uid(self):
        if hasattr(self, "base") and self.base:
            return self.base.uid

    def callback(self, cmd_string):
        self.app.ui.parse(cmd_string)

    def highlight(self, do_highlight=True):
        # Find corresponding highlight widget.
        current_highlight = None
        for c in self.app.root.ids.layout.children:
            if isinstance(c, HelpHighlight) and c.name == self.hostname:
                current_highlight = c
                break

        if not current_highlight and do_highlight:
            # Add highlight.
            # logging.debug(f"GUI: add highlight for {self.hostname}")
            # Set draw index one higher than (i.e. behind) Device.
            idx = self.parent.children.index(self) + 1
            self.app.root.ids.layout.add_widget(
                HelpHighlight(center=self.center, name=self.hostname), idx
            )
        elif current_highlight and not do_highlight:
            # Remove highlight.
            logging.debug(f"GUI: remove highlight for {self.hostname}")
            self.app.root.ids.layout.remove_widget(current_highlight)

    def hide(self, do_hide=True):
        # Ensure base object state matches GUI object state.
        self.base.is_invisible = do_hide
        if do_hide:
            # Hide any help highlight.
            self.highlight(False)
        elif do_hide is False:
            # Show help highlight if relevant.
            self.app.update_help_highlight_devices()
        # Hide/show any links.
        for lnk in self.links:
            lnk.hide(do_hide)
        # Hide/show self.
        hide_widget(self, do_hide)

    def new(self):
        raise NotImplementedError
        self._set_uid()
        self.set_type()
        self.set_location()
        self.set_hostname()

    def on_pos(self, *args):
        # Set initial position for comparison later.
        # NOTE: pos is set in 2 steps: x first, then y, and `pos` is modified
        # each time. So we have to wait until both x and y values are nonzero
        # before setting the true initial position.
        if 0 in self.pos_init:
            self.pos_init = (self.x, self.y)
        # Show if hidden and not in initial position.
        if self.opacity == 0 and (self.x, self.y) != self.pos_init:
            self.hide(False)
        # Nullify pos_hint when initial position is changed to allow for widget
        # to be drag-n-dropped.
        self.pos_hint = {}
        # Move help device highlighting with device.
        self.app.update_help_highlight_devices()
        # Move links' ends with device.
        for lnk in self.links:
            lnk.hide(False)
            lnk.move_connection(self)

    def on_press(self):
        self._build_commands_popup().open()

    def set_power_status(self, *args):
        if self.base.powered_on:
            self.canvas.after.clear()
        else:
            pos = (self.button.x + self.button.width - dp(15), self.button.y + dp(5))
            with self.canvas.after:
                Color(rgb=(1, 0, 0))
                Ellipse(pos=pos, size=(dp(8), dp(8)))

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
                    title=f"{_('Ping [host] from')} {self.hostname}"
                ).open
            elif command == _("Edit"):
                cb = EditDevicePopup(title=_("Edit device"), device=self).open
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

    def _set_image(self):
        devices = NETWORK_ITEMS.get("devices").get("user") | NETWORK_ITEMS.get(
            "devices"
        ).get("infrastructure")
        img = devices.get(self.base.json.get("mytype")).get("img")
        if img is None:
            raise TypeError(f"Unhandled device type: {self.base.json.get('mytype')}")
        self.button.background_normal = str(self.app.IMAGES / img)

    def _set_pos(self, rel_pos=None):
        if rel_pos is None:
            rel_pos = location_to_rel_pos(self.base.json.get("location"))
        self.pos_hint = {"center": rel_pos}


class CommandsPopup(AppPopup):
    pass


class EditDevicePopup(AppPopup):
    def __init__(self, device, **kwargs):
        self.device = device
        super().__init__(**kwargs)

    def on_gateway(self):
        raise NotImplementedError

    def on_routes(self):
        raise NotImplementedError

    def on_vlans(self):
        raise NotImplementedError

    def on_nics_edit(self):
        raise NotImplementedError

    def on_nic_selection(self, selected_nic):
        self._set_ips(selected_nic)

    def on_ips_add(self):
        raise NotImplementedError

    def on_ips_remove(self):
        raise NotImplementedError

    def on_ips_edit(self):
        raise NotImplementedError

    def on_okay(self):
        logging.debug("GUI: TODO: Apply config updates on exit.")
        raise NotImplementedError

    def _set_ips(self, selected_nic):
        for n in self.device.nics:
            if n.name == selected_nic:
                for iface in n.interfaces:
                    if iface.get("nicname") == n.name:
                        print(f"{iface.get('myip')=}")
                        ipdata = iface.get("myip")
                        ip = ipdata.get("ip")
                        if ip.startswith("0"):
                            self.ids.ip_list.text = ""
                        else:
                            self.ids.ip_list.text = f"{ip}/{ipdata.get('mask')}"
                        break
                break


class NICsRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = {}

    def update_data(self, nics):
        self.data = [{"text": n.name} for n in nics if not n.name.startswith("lo")]

    def on_selection(self, index):
        self.root.on_nic_selection(self.data[index].get("text"))


class PingHostPopup(AppPopup):
    def on_cancel(self):
        self.dismiss()

    def on_okay(self, text):
        self.app.ui.parse(f"ping {self.title.split()[-1]} {text}")
        self.dismiss()
