import ipaddress

from .core import ItemBase

LOCALHOST_IP = "127.0.0.1"
UNSET_IP = "0.0.0.0"
UNSET_IP_CONFIG = {
    "ip": UNSET_IP,
    "mask": "255.255.255.0",
    "gateway": "0.0.0.0",
    "type": "route",
}


class Interface(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)

    @property
    def ip_data(self) -> dict:
        return self.json.get("myip")

    @ip_data.setter
    def ip_data(self, data):
        self.json["myip"] = data

    @property
    def ipaddress(self) -> dict:
        tAddr = IpAddress(self.ip_data)
        try:
            return ipaddress.ip_interface(tAddr.address + "/" + tAddr.netmask)
        except ValueError:
            return None

    @property
    def nicname(self) -> str:
        return self.json.get("nicname")

    @nicname.setter
    def nicname(self, value):
        self.json["nicname"] = value

    @property
    def vlans(self):
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
