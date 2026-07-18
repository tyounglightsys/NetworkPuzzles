from .core import ItemBase


class Route(ItemBase):
    NEW = {
        "ip": "",
        "mask": "",
        "gateway": None,
        "interface": None,
        "nic": None,
        "type": "route",
    }

    def __init__(self, json_data=None, gateway=None, ip=None, netmask=None):
        if json_data is None:
            json_data = self.NEW.copy()
        super().__init__(json_data)
        if gateway:
            self.gateway = gateway
        if ip:
            self.ip = ip
        if netmask:
            self.netmask = netmask
        self.metric = None  # maybe useful in the future?

    def __str__(self):
        network = "default"
        if self.network:
            network = self.network
        s = network
        if self.gateway:
            s += f" via {self.gateway}"
        if self.interface:
            s += f" dev {self.interface.get('myip').get('ip')}"
        if self.metric:
            s += f" metric {self.metric}"
        return s

    @property
    def gateway(self):
        return self.json.get("gateway")

    @gateway.setter
    def gateway(self, value):
        self.json["gateway"] = value

    @property
    def interface(self):
        return self.json.get("interface")

    @interface.setter
    def interface(self, value):
        self.json["interface"] = value

    @property
    def ip(self):
        return self.json.get("ip")

    @ip.setter
    def ip(self, value):
        self.json["ip"] = value

    @property
    def netmask(self):
        return self.json.get("mask")

    @netmask.setter
    def netmask(self, value):
        self.json["mask"] = value

    @property
    def network(self):
        if self.ip and self.netmask:
            return f"{self.ip}/{self.netmask}"
        else:
            return None

    @property
    def nic(self):
        return self.json.get("nic")

    @nic.setter
    def nic(self, value):
        self.json["nic"] = value

    @property
    def type(self):
        return self.json.get("type")

    @type.setter
    def type(self, value):
        self.json["type"] = value
