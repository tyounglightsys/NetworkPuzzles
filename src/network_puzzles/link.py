from .core import ItemBase


class Link(ItemBase):
    def __init__(self, json_data=None):
        super().__init__(json_data)

    def __str__(self):
        return self.hostname

    @property
    def dest(self) -> str:
        return self.json.get("DstNic").get("hostname", "")

    @property
    def dest_nic(self):
        return self.json.get("DstNic")

    @property
    def hostname(self) -> str:
        return self.json.get("hostname", "")

    @property
    def linktype(self) -> str:
        return self.json.get("linktype", "")

    @property
    def src(self) -> str:
        return self.json.get("SrcNic").get("hostname", "")

    @property
    def src_nic(self):
        return self.json.get("SrcNic")

    @property
    def uniqueidentifier(self) -> str:
        return self.json.get("uniqueidentifier", "")
