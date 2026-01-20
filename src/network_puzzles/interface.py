from .core import ItemBase


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
