# import logging
import random

from . import interface, session
from .core import ItemBase
from .link import Link


class Nic(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)
        self._can_use_dhcp = None

    def __str__(self):
        return self.name

    @property
    def can_use_dhcp(self):
        if self._can_use_dhcp is None:
            if self.type in ("eth", "management_interface", "wlan"):
                self._can_use_dhcp = True
            else:
                self._can_use_dhcp = False
        return self._can_use_dhcp

    @can_use_dhcp.setter
    def can_use_dhcp(self, value):
        self._can_use_dhcp = value

    @property
    def interfaces(self):
        if not isinstance(self.json.get("interface"), list):
            self.json["interface"] = [self.json.get("interface")]
        return self.json.get("interface")

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
    def my_id(self):
        """Object with "myid" data."""
        return MyId(self.json.get("myid"))

    @property
    def name(self):
        return self.json.get("nicname", "")

    @name.setter
    def name(self, value):
        self.json["nicname"] = value

    @property
    def type(self):
        # NOTE: The JSON data defines nictype as a list of two identical
        # strings. We simply return the first one.
        if self.json.get("nictype") is None:
            self.type = ""
        return self.json.get("nictype")[0]

    @type.setter
    def type(self, value):
        self.json["nictype"] = [value, value]

    @property
    def uniqueidentifier(self):
        return self.json.get("uniqueidentifier", "")

    @property
    def encryption_key(self):
        if self.json.get("encryptionkey") is None:
            # Some JSON files have this set as `null`, which translates to
            # `None`, but we need a string for GUI use.
            self.json["encryptionkey"] = ""
        return self.json.get("encryptionkey", "")

    @encryption_key.setter
    def encryption_key(self, value: str):
        # Key can't contain "," because parser replaces "," with " " during
        # tokenization.
        if "," in value:
            raise ValueError("Invalid character: ,")
        self.json["encryptionkey"] = value

    @property
    def ssid(self):
        return self.json.get("ssid", "")

    @ssid.setter
    def ssid(self, value: str):
        self.json["ssid"] = value

    @property
    def endpoint(self):
        return self.tunnel_endpoint.get("ip", "")

    @endpoint.setter
    def endpoint(self, value: str):
        self.tunnel_endpoint["ip"] = value

    @property
    def tunnel_endpoint(self):
        if self.json.get("tunnelendpoint") is None:
            self.json["tunnelendpoint"] = {}
        return self.json.get("tunnelendpoint")

    @property
    def uses_dhcp(self):
        if self.json.get("usesdhcp") is None:
            self.json["usesdhcp"] = "false"
        return self.json.get("usesdhcp").lower() in ["true", "yes"]

    @uses_dhcp.setter
    def uses_dhcp(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["usesdhcp"] = value

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

    def get_connected_link(self):
        """Find a link connected to the specified network card"""
        # logging.debug(
        #    f"looking for link connected to nic; #{self.my_id.nic_id}; {self.name}"
        # )
        for one in session.puzzle.links:
            if one:
                # print ("   link - " + one['hostname'])
                if one["SrcNic"]["nicid"] == self.my_id.nic_id:
                    return one
                if one["DstNic"]["nicid"] == self.my_id.nic_id:
                    return one
        # we did not find anything that matched.  Return None
        return None

    def is_connected(self):
        """Connected status of given interface.
        returns: boolean
        """
        for link_data in session.puzzle.links:
            link = Link(link_data)
            # Check if NIC is used by host device as src or dest.
            if self.my_id.hostname == link.src and self.name == link.src_nic.get(
                "nicname"
            ):  # NIC used as link src
                if link.linktype == "broken":
                    return False
                else:
                    return True
            if self.my_id.hostname == link.dest and self.name == link.dest_nic.get(
                "nicname"
            ):  # NIC used as link dest
                if link.linktype == "broken":
                    return False
                else:
                    return True
        return False


class MyId(ItemBase):
    """Helper class for accessing NIC "myid" data."""

    def __init__(self, json_data=None):
        super().__init__(json_data)

    @property
    def host_id(self):
        return self.json.get("hostid")

    @property
    def hostname(self):
        return self.json.get("hostname")

    @property
    def nic_id(self):
        return self.json.get("nicid")

    @property
    def nicname(self):
        return self.json.get("nicname")
