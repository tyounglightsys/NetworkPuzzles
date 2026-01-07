import logging

from kivy.uix.popup import Popup

from .. import device, session
from .inputs import ValueInput
from .labels import CheckBoxLabel
from .layouts import SingleRowLayout
from .views import PuzzlesRecView  # needed by PuzzleChooserPopup #  noqa: F401


class ThemedPopup(Popup):
    def __init__(self, **kwargs):
        # TODO: This popup automatically generates a GridLayout with 3 child
        # widgets: BoxLayout, Widget, Label. Better to set the content
        # explicitly when the popup is instantiated elsewhere.
        super().__init__(**kwargs)

    @property
    def app(self):
        return session.app


class ActionPopup(ThemedPopup):
    def on_cancel(self):
        self.dismiss()

    def on_okay(self):
        self.dismiss()


class ChooseNicPopup(ActionPopup):
    def __init__(self, devicew, **kwargs):
        self.device = devicew
        super().__init__(**kwargs)
        self.selected_nic = None
        free_nics = [
            n for n in self.device.nics if device.linkConnectedToNic(n.json) is None
        ]
        self.ids.nics_list.update_data(free_nics, management=False)

    def on_nic_selection(self, selected_nic_text):
        # Strip MAC info from NIC text.
        self.selected_nic = selected_nic_text.split(";")[0]

    def on_okay(self):
        self.app.chosen_nic = self.selected_nic
        super().on_okay()


class CommandPopup(ActionPopup):
    def on_okay(self):
        self.app.ui.parse(self.ids.text_input.text)
        super().on_okay()
        # self.dismiss()


class DeviceCommandsPopup(ThemedPopup):
    pass


class EditDhcpPopup(ActionPopup):
    def __init__(self, devicew, **kwargs):
        self.device = devicew
        super().__init__(**kwargs)
        self.dhcp_configs = [
            ip_data
            for ip_data in self.device.json.get("dhcprange", list())
            if ip_data.get("ip") != "127.0.0.1"
        ]
        self._add_dhcp_configs()

    def on_okay(self):
        for c in self.dhcp_configs:
            ip = c.get("ip")
            row = self._get_dhcp_row(ip)
            if row:
                start = row.children[-2].text
                end = row.children[-3].text
                if start != c.get("mask") or end != c.get("gateway"):
                    cmd = f"set {self.device.hostname} dhcp {ip} {start}-{end}"
                    logging.info(f"Popups: > {cmd}")
                    self.app.ui.parse(cmd)

        # Update GUI helps b/c it will trigger tooltip updates, which are needed
        # b/c IP data has likely changed.
        self.app.update_help()
        super().on_okay()

    def _add_dhcp_configs(self):
        for config in self.dhcp_configs:
            bl = SingleRowLayout()
            ip = CheckBoxLabel(text=config.get("ip"))
            start = ValueInput(text=config.get("mask"))
            end = ValueInput(text=config.get("gateway"))
            for w in [ip, start, end]:
                bl.add_widget(w)
        self.ids.dhcp_configs_layout.add_widget(bl)

    def _get_dhcp_row(self, ip):
        for row in self.ids.dhcp_configs_layout.children:
            if row.children[-1].text == ip:
                return row


class EditIpPopup(ActionPopup):
    def __init__(self, device_popup, ip_address, **kwargs):
        self.device_popup = device_popup
        self.ip_address = ip_address
        super().__init__(**kwargs)

    def on_okay(self):
        # Add updating command.
        self.device_popup.puzzle_commands.append(
            f"set {self.device_popup.device.hostname} {self.device_popup.selected_nic} {self.ip_address.address}/{self.ip_address.netmask}"
        )
        # Update IPs in IPs list.
        self.device_popup._set_ips()
        super().on_okay()

    def set_address(self, input_inst):
        if not input_inst.focus:
            self.ip_address.address = input_inst.text

    def set_netmask(self, input_inst):
        if not input_inst.focus:
            self.ip_address.netmask = input_inst.text

    def set_gateway(self, input_inst):
        if not input_inst.focus:
            self.ip_address.gateway = input_inst.text


class ExceptionPopup(ThemedPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message

    def on_dismiss(self):
        # Don't allow the app to continue running.
        self.app.stop()


class PingHostPopup(ActionPopup):
    def __init__(self, dev, **kwargs):
        self.device = dev
        super().__init__(**kwargs)

    def on_okay(self, dest):
        self.app.ui.parse(f"ping {self.device.hostname} {dest}")
        super().on_okay()


class PuzzleChooserPopup(ActionPopup):
    def on_load(self):
        self.app.selected_puzzle = self.ids.puzzles_view.selected_item.get("text")
        self.app.setup_puzzle()
        super().on_okay()


class PuzzleCompletePopup(ActionPopup):
    pass
