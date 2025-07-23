class Interface:
    def __init__(self, interfacerec=None):
        if interfacerec is None:
            interfacerec = {}
        self.json = interfacerec
        self.ip: str = self.json.get("myip")
        self.vlan: list = []
        if "VLAN" in self.json:
            if not isinstance(self.json.get("VLAN"), list):
                self.json["VLAN"] = [self.json.get("VLAN")]
            for onevlan in self.json.get("VLAN"):
                self.vlan.append(
                    onevlan
                )  # we do not need to do a deep copy or anything

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


class IpAddress:
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.json = data

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
