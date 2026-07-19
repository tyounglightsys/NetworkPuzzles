import ipaddress
from copy import deepcopy

from .core import ItemBase

BROADCAST_MAC = "FFFFFFFFFFFF"
GENERIC_IP4 = "0.0.0.0"
LOCALHOST_IP4 = "127.0.0.1"
BROADCAST_IP4 = "255.255.255.255"
UNSET_IP4_CONFIG = {
    "ip": GENERIC_IP4,
    "mask": "255.255.255.0",
    "gateway": GENERIC_IP4,
    "type": "route",
}


class Interface(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)
        self._ipaddress = None
        self._ip_obj = None

    @property
    def ip(self) -> str:
        return self.ip_obj.address

    @property
    def ip_data(self) -> dict:
        return self.json.get("myip")

    @ip_data.setter
    def ip_data(self, data):
        self.json["myip"] = data

    @property
    def ip_obj(self):
        if self._ip_obj is None:
            self._ip_obj = IpAddress(self.ip_data)
        return self._ip_obj

    @property
    def ipaddress(self) -> dict:
        if self._ipaddress is None:
            try:
                self._ipaddress = ipaddress.ip_interface(
                    f"{self.ip_obj.address}/{self.ip_obj.netmask}"
                )
            except ValueError:
                pass
        return self._ipaddress

    @property
    def netmask(self) -> str:
        return self.ip_obj.netmask

    @property
    def nicname(self) -> str:
        return self.json.get("nicname")

    @nicname.setter
    def nicname(self, value):
        self.json["nicname"] = value

    @property
    def vlans_data(self):
        if "VLAN" not in self.json:
            self.json["VLAN"] = []
        elif not isinstance(self.json.get("VLAN"), list):
            self.json["VLAN"] = [self.json.get("VLAN")]
        return self.json.get("VLANS")

    def begin_ingress(self, pkt):
        """Here we would do anything needed to be done with the interface.
        VLAN
        SSID
        Tunnel/VPN
        """
        # right now, we let pass it back
        return True


class IpAddress(ItemBase):
    def __init__(self, json_data=None):
        if json_data is None:
            json_data = deepcopy(UNSET_IP4_CONFIG)
        super().__init__(json_data)

    @property
    def address(self) -> str:
        return self.json.get("ip")

    @address.setter
    def address(self, value):
        self.json["ip"] = value

    @property
    def netmask(self) -> str:
        return self.json.get("mask")

    @netmask.setter
    def netmask(self, value):
        self.json["mask"] = value

    @property
    def gateway(self) -> str:
        return self.json.get("gateway")

    @gateway.setter
    def gateway(self, value):
        self.json["gateway"] = value

    def __str__(self):
        return (
            f"{self.__class__.__name__}({self.address}/{self.netmask} {self.gateway})"
        )
