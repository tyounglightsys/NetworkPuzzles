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


class DevicePopup(ActionPopup):
    def __init__(self, device=None, **kwargs):
        if device is None:
            raise ValueError('DevicePopup requires "device" kwarg.')
        self.device = device
        super().__init__(**kwargs)


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


class ChooseNicPopup(DevicePopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_nic = None
        free_nics = [n for n in self.device.nics if n.get_connected_link() is None]
        self.ids.nics_list.update_data(free_nics, management=False)

    def on_nic_selection(self, selected_nic):
        self.selected_nic = selected_nic.get("data")

    def on_okay(self):
        self.app.chosen_nic = self.selected_nic.name
        super().on_okay()


class CommandPopup(ActionPopup):
    def on_okay(self):
        self.app.ui.parse(self.ids.text_input.text)
        super().on_okay()


class DeviceCommandsPopup(ThemedPopup):
    pass


class EditDhcpPopup(DevicePopup):
    def __init__(self, **kwargs):
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

    def on_okay(self, *args):
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
            start.bind(focus=start.schedule_select_all)
            start.bind(on_text_validate=self.on_okay)
            end = ValueInput(text=data.get("gateway"))
            end.bind(focus=end.schedule_select_all)
            end.bind(on_text_validate=self.on_okay)
            for w in [ip, start, end]:
                bl.add_widget(w)
            self.ids.dhcp_configs_layout.add_widget(bl)


class EditFirewallPopup(DevicePopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_rule = None

    def on_open(self):
        self.ids.firewall_rules_list.update_data()

    def on_rule_selection(self, rule_data):
        self.selected_rule = rule_data
        self.ids.edit_button.disabled = False
        self.ids.remove_button.disabled = False

    def on_edit_rule(self):
        if self.selected_rule:
            raise NotImplementedError

    def on_add_rule(self):
        raise NotImplementedError

    def on_remove_rule(self):
        if self.selected_rule:
            logging.debug(f"Popups: {self.selected_rule=}")
            rule_data = self.selected_rule.get("data")
            src = rule_data.get("source")
            dst = rule_data.get("destination")
            action = rule_data.get("action").lower()
            cmd = f"firewall {self.device.hostname} del {src} {dst} {action}"
            # TODO: This will be obsolete when undo becomes based on states.
            self.device.firewall_rules.remove(rule_data)
            self.app.ui.parse(cmd)
            self.ids.firewall_rules_list.update_data()


class EditIpPopup(BaseIpPopup):
    def __init__(self, device_popup, **kwargs):
        super().__init__(**kwargs)
        self.ids.gateway_input.disabled = True
        self.device_popup = device_popup

    def on_okay(self):
        # Add updating command.
        self.app.commands_queue.append(
            f"set {self.device_popup.device.hostname} {self.device_popup.selected_nic.name} {self.ip_address.address}/{self.ip_address.netmask}"
        )
        # Update IPs in IPs list.
        self.device_popup._set_ips()
        super().on_okay()


class EditNicPopup(DevicePopup):
    def __init__(self, nic, **kwargs):
        self.nic = nic
        super().__init__(**kwargs)
        self.encryption_key_orig = self.nic.encryption_key
        self.endpoint_orig = self.nic.endpoint

    def on_okay(self):
        if self.nic.encryption_key != self.encryption_key_orig:
            self.app.commands_queue.append(
                f"set {self.device.hostname} key {self.nic.name} {self.nic.encryption_key}"
            )
        if self.nic.endpoint != self.endpoint_orig:
            self.app.commands_queue.append(
                f"set {self.device.hostname} endpoint {self.nic.name} {self.nic.endpoint}"
            )
        super().on_okay()

    def on_uses_dhcp(self, inst):
        self.nic.uses_dhcp = inst.active

    def set_endpoint(self, input_inst):
        if not input_inst.focus:
            self.nic.endpoint = input_inst.text

    def set_encryption_key(self, input_inst):
        if not input_inst.focus:
            self.nic.encryption_key = input_inst.text


class EditRoutesPopup(DevicePopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_route = None

    def on_open(self):
        self.ids.nic_routes_list.update_data()
        self.ids.static_routes_list.update_data(static=True)

    def on_route_selection(self, route_data, inst):
        if inst is self.ids.static_routes_list.__ref__():
            self.selected_route = route_data
            self.ids.edit_button.disabled = False
            self.ids.remove_button.disabled = False

    def on_add(self):
        NewRoutePopup(self).open()

    def on_edit(self):
        # FIXME
        logging.debug(f'TEST: "Edit" clicked; selected route: "{self.selected_route}"')
        raise NotImplementedError

    def on_remove(self):
        # FIXME
        logging.debug(f'TEST: "-" clicked; selected route: "{self.selected_route}"')
        raise NotImplementedError


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
        dev = self.routes_popup.device.hostname
        ip = self.ip_address.address
        mask = self.ip_address.netmask
        gw = self.ip_address.gateway
        # Update intermediate popup data.
        self.routes_popup.device.route_add(f"{ip}/{mask}", gw)
        self.routes_popup.ids.static_routes_list.update_data(static=True)
        # Update puzzle data
        self.app.ui.parse(f"route {dev} add {ip}/{mask} {gw}")
        super().on_okay()


class PingHostPopup(DevicePopup):
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
