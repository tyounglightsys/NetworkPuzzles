import re


class Link:
    def __init__(self, linkrec={}):
        self.json = linkrec

    @property
    def dest(self):
        return self.json.get("DstNic").get("hostname")

    @property
    def hostname(self):
        return self.json.get("hostname")

    @hostname.setter
    def hostname(self, name):
        self.json["hostname"] = name

    @property
    def src(self):
        return self.json.get("SrcNic").get("hostname")
