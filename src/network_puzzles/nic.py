import random

from . import interface


class Nic:
    def __init__(self, nicrec):
        if not isinstance(nicrec, dict):
            raise ValueError(f"Invalid JSON data passed to {self.__class__}.")
        self.json = nicrec
        # add the interfaces
        if not isinstance(self.json.get("interface"), list):
            self.json["interface"] = [
                self.json["interface"]
            ]  # make it a list so we can iterate it

    @property
    def interfaces(self):
        data = self.json.get("interface")
        if not isinstance(data, list):
            data = [data]
        return [iface for iface in data]

    @property
    def ip_addresses(self):
        ips = list()
        for iface_data in self.interfaces:
            iface = interface.Interface(iface_data)
            if iface.nicname == self.name:
                ip_addr = interface.IpAddress(iface.ip_data)
                if not ip_addr.address.startswith("0"):
                    ips.append(iface.ip_data)
                break
        return ips

    @property
    def mac(self):
        return self.json.get("Mac")

    @property
    def myid(self):
        return self.json.get("myid")

    @property
    def name(self):
        return self.json.get("nicname")

    @property
    def type(self):
        return self.json.get("nictype")

    @property
    def uses_dhcp(self):
        return self.json.get("usesdhcp").lower() in ["true", "yes"]

    def ensure_mac(self, data=None):
        if data is not None:
            new_data = data
        else:
            new_data = self.json

        if "Mac" not in new_data:
            # Most of the network cards do not have this done yet.  We generate a new random one
            localmac = ""
            for i in range(1, 13):
                localmac = localmac + random.choice("ABCDEF1234567890")
            new_data["Mac"] = localmac

        self.json = new_data
        return new_data
