import logging
from copy import deepcopy

from kivy.uix.popup import Popup

from .. import interface, nic, session
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


class BaseIpPopup(ActionPopup):
    """Base class for IP-address-related popups."""

    def __init__(self, ip_address=None, **kwargs):
        if ip_address is None:
            ip_address = interface.IpAddress(deepcopy(interface.UNSET_IP_CONFIG))
        self.ip_address = ip_address
        super().__init__(**kwargs)

    def set_address(self, input_inst):
        if not input_inst.focus:
            self.ip_address.address = input_inst.text

    def set_netmask(self, input_inst):
        if not input_inst.focus:
            self.ip_address.netmask = input_inst.text

    def set_gateway(self, input_inst):
        if not input_inst.focus:
            self.ip_address.gateway = input_inst.text


class ChooseNicPopup(ActionPopup):
    def __init__(self, devicew, **kwargs):
        self.device = devicew
        super().__init__(**kwargs)
        self.selected_nic = None
        free_nics = [n for n in self.device.nics if n.get_connected_link() is None]
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


class DeviceCommandsPopup(ThemedPopup):
    pass


class EditDhcpPopup(ActionPopup):
    def __init__(self, devicew, **kwargs):
        self.device = devicew
        super().__init__(**kwargs)
        self._add_dhcp_configs()

    @property
    def dhcp_configs(self):
        return [
            ip_data
            for ip_data in self.device.json.get("dhcprange", [])
            if ip_data.get("ip") != interface.LOCALHOST_IP
        ]

    @property
    def unset_configs(self):
        unset_configs = []
        for data in self.device.all_nics():
            n = nic.Nic(data)
            ips = [
                ip.get("ip")
                for ip in n.ip_addresses
                if ip.get("ip") != interface.LOCALHOST_IP
            ]
            for ip in ips:
                _data = deepcopy(interface.UNSET_IP_CONFIG)
                _data["ip"] = ip
                unset_configs.append(_data)
        if len(unset_configs) == 0:
            data = deepcopy(interface.UNSET_IP_CONFIG)
            data["ip"] = interface.UNSET_IP
            unset_configs.append(data)
        return unset_configs

    def on_okay(self):
        old_configs = [c.values() for c in self.dhcp_configs]
        for row in self.ids.dhcp_configs_layout.children:
            # Child widgets' order is the opposite of how they were added.
            end, start, ip = [c.text for c in row.children]
            if ip == interface.UNSET_IP:
                # Fallback config.
                continue
            elif [ip, start, end] in old_configs:
                # Unchanged config.
                continue
            cmd = f"set {self.device.hostname} dhcp {ip} {start}-{end}"
            logging.info(f"Popups: > {cmd}")
            self.app.ui.parse(cmd)

        # Update GUI helps b/c it will trigger tooltip updates, which are needed
        # b/c IP data has likely changed.
        self.app.update_help()
        super().on_okay()

    def _add_dhcp_configs(self):
        configs = self.dhcp_configs
        if len(configs) == 0:
            configs = self.unset_configs
        for data in configs:
            bl = SingleRowLayout()
            ip = CheckBoxLabel(text=data.get("ip"))
            start = ValueInput(text=data.get("mask"))
            end = ValueInput(text=data.get("gateway"))
            for w in [ip, start, end]:
                bl.add_widget(w)
            self.ids.dhcp_configs_layout.add_widget(bl)


class EditIpPopup(BaseIpPopup):
    def __init__(self, device_popup, ip_address, **kwargs):
        super().__init__(ip_address=ip_address, **kwargs)
        self.ids.gateway_input.disabled = True
        self.device_popup = device_popup

    def on_okay(self):
        # Add updating command.
        self.device_popup.puzzle_commands.append(
            f"set {self.device_popup.device.hostname} {self.device_popup.selected_nic} {self.ip_address.address}/{self.ip_address.netmask}"
        )
        # Update IPs in IPs list.
        self.device_popup._set_ips()
        super().on_okay()


class EditNicPopup(ActionPopup):
    def __init__(self, device_popup, nic, **kwargs):
        self.device_popup = device_popup
        self.nic = nic
        super().__init__(**kwargs)

    def on_okay(self):
        # set firewall1 key vpn0 Key
        self.device_popup.puzzle_commands.append(
            f"set {self.device_popup.device.hostname} key {self.device_popup.selected_nic} {self.nic.encryption}"
        )
        super().on_okay()

    def on_uses_dhcp(self, inst):
        self.nic.uses_dhcp = inst.active

    def set_encryption_key(self, input_inst):
        if not input_inst.focus:
            self.nic.encryption = input_inst.text


class EditRoutesPopup(ActionPopup):
    def __init__(self, device_popup, **kwargs):
        self.device_popup = device_popup
        super().__init__(**kwargs)
        self.ids.nic_routes_list.set_routes(
            self.device_popup.device.get_routes_from_nics()
        )
        self.ids.static_routes_list.set_routes(self.device_popup.device.routes)

    def check_for_selection(self, inst):
        if inst.selected_item:
            self.ids.edit_button.disabled = False

    def on_edit(self):
        route = self.ids.static_routes_list.selected_item
        logging.debug(f'TEST: "Edit" clicked; "{route}" selected')

    def on_new(self):
        NewRoutePopup(self).open()


class ExceptionPopup(ThemedPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message
        logging.error(message)

    # def on_dismiss(self):
    #     # Don't allow the app to continue running.
    #     self.app.stop()


class NewRoutePopup(BaseIpPopup):
    def __init__(self, routes_popup, **kwargs):
        self.routes_popup = routes_popup
        super().__init__(**kwargs)

    def on_okay(self):
        # logging.debug(f"{self.ip_address=}")
        dev = self.routes_popup.device_popup.device.hostname
        ip = self.ip_address.address
        mask = self.ip_address.netmask
        gw = self.ip_address.gateway
        # Update intermediate popup data.
        self.routes_popup.device_popup.device.route_add(f"{ip}/{mask}", gw)
        self.routes_popup.ids.static_routes_list.update_data()
        # Update puzzle data
        self.app.ui.parse(f"route {dev} add {ip}/{mask} {gw}")
        super().on_okay()


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
