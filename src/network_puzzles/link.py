class Link:
    def __init__(self, linkrec={}):
        self.json = linkrec

    @property
    def dest(self):
        return self.json.get("DstNic").get("hostname")

    @property
    def hostname(self):
        return self.json.get("hostname")

    @property
    def linktype(self):
        return self.json.get("linktype")

    @property
    def src(self):
        return self.json.get("SrcNic").get("hostname")

    @property
    def uniqueidentifier(self):
        return self.json.get("uniqueidentifier")
