import copy
from .interface import Interface

class Nic:
    nictype: str
    nicname: str
    uniqueidentifier: str
    myid: dict
    usesdhcp: str
    
    def __init__(self, nicrec):
        self.nictype = nicrec.get('nictype')
        self.nicname = nicrec.get('nicname')
        self.uniqueidentifier = nicrec.get('uniqueidentifier')
        self.myid = copy.copy(nicrec.get('myid'))
        self.usesdhcp = nicrec.get('usesdhcp')
        self.ssid = nicrec.get('ssid')
        self.interface = []
        #add the interfaces
        if not isinstance(nicrec.get('interface'), list):
            nicrec['interface'] = [nicrec['interface']] #make it a list so we can itterate it
        for oneinterface in nicrec.get('interface'):
            tinterface = Interface(oneinterface)
            self.interface.append(tinterface)

