from . import session
from .core import ItemBase, get_puzzle_distance


class EndNic(ItemBase):
    """Endpoint NIC as defined for a link; not to be confused with `nic.Nic`"""

    # a link nic rec looks like: { "hostid": "100", "nicid": "102", "hostname": "pc0", "nicname": "eth0" }

    def __init__(self, json_data=None):
        super().__init__(json_data)

    def __str__(self) -> str:
        return f"{self.host_name}:{self.nic_name}"

    @property
    def host_id(self) -> str:
        return self.json.get("hostid")

    @property
    def host_name(self) -> str:
        return self.json.get("hostname")

    @property
    def nic_id(self) -> str:
        return self.json.get("nicid")

    @property
    def nic_name(self) -> str:
        return self.json.get("nicname")

    @property
    def device(self):
        return session.puzzle.device_obj_from_name(self.host_name)


class Link(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)

    def __str__(self):
        return self.hostname

    @property
    def dest(self) -> str:
        return self.dest_nic.host_name if self.dest_nic else ""

    @property
    def dest_nic(self):
        return EndNic(self.json.get("DstNic"))

    @property
    def dest_nic_name(self):
        return self.dest_nic.nic_name if self.dest_nic else ""

    @property
    def distance(self):
        """Return the distance between link endpoints"""
        # NOTE: Assumes link travels in a straight line.
        if self.src_nic.device and self.dest_nic.device:
            return get_puzzle_distance(
                *self.src_nic.device.location, *self.dest_nic.device.location
            )

    @property
    def hostname(self) -> str:
        return self.json.get("hostname", "")

    @property
    def linktype(self) -> str:
        return self.json.get("linktype", "")

    @property
    def src(self) -> str:
        return self.src_nic.host_name if self.src_nic else ""

    @property
    def src_nic(self):
        return EndNic(self.json.get("SrcNic"))

    @property
    def src_nic_name(self):
        return self.src_nic.nic_name if self.src_nic else ""

    @property
    def uniqueidentifier(self) -> str:
        return self.json.get("uniqueidentifier", "")

    def show_info(self):
        """Print information about the link to the in-app terminal."""
        session.print("----Link----")
        session.print(f"name: {self.hostname}")
        session.print(f"type: {self.linktype}")
        session.print(f"source: {self.src} - {self.src_nic_name}")
        session.print(f"dest: {self.dest} - {self.dest_nic_name}")
