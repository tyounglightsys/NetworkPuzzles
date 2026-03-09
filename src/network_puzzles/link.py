from . import session
from .core import ItemBase


class Link(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)

    def __str__(self):
        return self.hostname

    @property
    def dest(self) -> str:
        return self.dest_nic.get("hostname", "")

    @property
    def dest_nic(self):
        return self.json.get("DstNic")

    @property
    def dest_nic_name(self):
        return self.dest_nic.get("nicname", "")

    @property
    def hostname(self) -> str:
        return self.json.get("hostname", "")

    @property
    def linktype(self) -> str:
        return self.json.get("linktype", "")

    @property
    def src(self) -> str:
        return self.src_nic.get("hostname", "")

    @property
    def src_nic(self):
        return self.json.get("SrcNic")

    @property
    def src_nic_name(self):
        return self.src_nic.get("nicname", "")

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
