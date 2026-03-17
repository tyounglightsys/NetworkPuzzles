import logging
from copy import deepcopy

from kivy.uix.popup import Popup

from .. import _, interface, nic, session
from .inputs import ValueInput
from .labels import CheckBoxLabel
from .layouts import SingleRowLayout
from .views import PuzzlesRecView  # needed by PuzzleChooserPopup #  noqa: F401


class ThemedPopup(Popup):
    @property
    def app(self):
        return session.app


class ActionPopup(ThemedPopup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_state = None
        if self.app.ui.puzzle:
            self.initial_state = deepcopy(self.app.ui.puzzle.json)

    def on_cancel(self):
        if self.initial_state:
            # Reset to previous state.
            logging.info('User clicked "Cancel". Resetting puzzle to pre-popup state.')
            self.app.ui.puzzle.json = self.initial_state
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


class DevicePopup(ActionPopup):
    def __init__(self, device=None, **kwargs):
        if device is None:
            raise ValueError('DevicePopup requires "device" kwarg.')
        self.device = device
        super().__init__(**kwargs)

    def on_okay(self):
        # FIXME: Update JSON data (will be obsolete after switch to state-based UNDO).
        self.device.json = self.app.ui.puzzle.device_from_name(self.device.hostname)
        super().on_okay()


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
        self.device_popup = device_popup
        super().__init__(**kwargs)
        self.ids.gateway_input.disabled = True

    def on_okay(self):
        # Run updating command.
        self.app.ui.parse(
            f"set {self.device_popup.device.hostname} {self.device_popup.selected_nic.name} {self.ip_address.address}/{self.ip_address.netmask}"
        )
        # Update IPs in IPs list.
        self.device_popup._set_ips()
        super().on_okay()


class EditNicPopup(DevicePopup):
    def __init__(self, current_nic=None, device_popup=None, **kwargs):
        if current_nic is None:
            current_nic = nic.Nic()
            current_nic.ensure_mac()
        self.nic = current_nic
        super().__init__(**kwargs)
        if device_popup is None:
            raise ValueError("Missing required kwarg 'device_popup'")
        self.device_popup = device_popup
        # Set title.
        if self.nic.name:
            self.title = f"{_('Edit')} {self.device.hostname}:{self.nic.name}"
        else:
            self.title = f"{_('Add NIC to')} {self.device.hostname}"
        self.encryption_key_orig = self.nic.encryption_key
        self.endpoint_orig = self.nic.endpoint

    def on_okay(self):
        if not self.nic.name:  # add NIC
            self.app.ui.parse(f"create nic {self.device.hostname} {self.nic.type}")
            # Get JSON for newly-created NIC (last listed).
            self.nic.name = self.device.all_nics()[-1].get("nicname")
        if self.nic.encryption_key != self.encryption_key_orig:
            self.app.ui.parse(
                f"set {self.device.hostname} key {self.nic.name} {self.nic.encryption_key}"
            )
        if self.nic.endpoint != self.endpoint_orig:
            self.app.ui.parse(
                f"set {self.device.hostname} endpoint {self.nic.name} {self.nic.endpoint}"
            )
        # Update NIC list.
        self.device_popup.ids.nics_list.update_data(self.device.nics, management=True)
        super().on_okay()

    def on_uses_dhcp(self, inst):
        self.nic.uses_dhcp = inst.active

    def set_endpoint(self, input_inst):
        if not input_inst.focus:
            self.nic.endpoint = input_inst.text

    def set_encryption_key(self, input_inst):
        if not input_inst.focus:
            self.nic.encryption_key = input_inst.text

    def set_nic_type(self, input_inst):
        if not input_inst.focus:
            self.nic.type = input_inst.text


class EditRoutePopup(BaseIpPopup):
    def __init__(self, routes_popup, **kwargs):
        self.routes_popup = routes_popup
        super().__init__(**kwargs)
        if "ip_address" not in kwargs.keys():
            self.old_target_ip = None
            self.old_gateway = None
        else:
            self.old_target_ip = f"{self.ip_address.address}/{self.ip_address.netmask}"
            self.old_gateway = self.ip_address.gateway

    def on_okay(self):
        # Remove focus from inputs so that variables are set.
        for w in (
            self.ids.ip_address_input,
            self.ids.netmask_input,
            self.ids.gateway_input,
        ):
            w.focus = False
        # logging.debug(f"{self.ip_address=}")
        target_ip = f"{self.ip_address.address}/{self.ip_address.netmask}"
        if self.old_target_ip:
            self.routes_popup._edit_route(
                self.old_target_ip, self.old_gateway, target_ip, self.ip_address.gateway
            )
        else:
            self.routes_popup._add_route(target_ip, self.ip_address.gateway)
        super().on_okay()


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
        EditRoutePopup(self).open()

    def on_edit(self):
        ip_address = interface.IpAddress(self.selected_route.get("data"))
        EditRoutePopup(self, ip_address=ip_address).open()

    def on_remove(self):
        route = self.selected_route.get("data")
        target_ip = f"{route.get('ip')}/{route.get('mask')}"
        gateway = route.get("gateway")
        self._remove_route(target_ip, gateway)

    def _add_route(self, target_ip, gateway):
        self._apply_route_action("add", target_ip, gateway)

    def _edit_route(self, old_target_ip, old_gw, new_target_ip, new_gw):
        self._remove_route(old_target_ip, old_gw)
        self._add_route(new_target_ip, new_gw)

    def _apply_route_action(self, action, target_ip, gateway):
        cmd = f"route {self.device.hostname} {action} {target_ip} {gateway}"
        self.app.ui.parse(cmd)
        # -----
        # TODO: The following will need to be removed once state-based UNDO is
        # implemented.
        if action.startswith("add"):
            self.device.route_add(target_ip, gateway)
        elif action.startswith("del"):
            self.device.route_del(target_ip, gateway)
        # -----
        self.ids.static_routes_list.update_data(static=True)

    def _remove_route(self, target_ip, gateway):
        self._apply_route_action("del", target_ip, gateway)


class ExceptionPopup(ThemedPopup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.ids.exception.text = message
        logging.error(message)

    # def on_dismiss(self):
    #     # Don't allow the app to continue running.
    #     self.app.stop()


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
