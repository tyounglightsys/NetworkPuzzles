import re


class Link:
    def __init__(self, linkrec={}):
        self.json = linkrec

    @property
    def dest(self):
        return self.hosts[1]

    @property
    def hostname(self):
        return self.json.get("hostname")

    @hostname.setter
    def hostname(self, name):
        self.json["hostname"] = name

    @property
    def hosts(self):
        return re.sub(r"(.*)_link_(.*)", r"\1|\2", self.hostname).split("|")

    @property
    def src(self):
        return self.hosts[0]
