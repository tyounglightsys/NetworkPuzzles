import copy
from interface import interface 

class nic:
    nictype = str
    nicname = str
    uniqueidentifier = str
    myid = {}
    usesdhcp = str
    
    def __init__(self, nicrec):
        self.nictype = nicrec['nictype']
        self.nicname = nicrec['nicname']
        self.uniqueidentifier = nicrec['uniqueidentifier']
        self.myid = copy.copy(nicrec['myid'])
        self.usesdhcp = nicrec['usesdhcp']
        self.ssid = nicrec['ssid']
        self.interface = []
        #add the interfaces
        if not isinstance(nicrec['interface'],list):
            nicrec['interface'] = [nicrec['interface']] #make it a list so we can itterate it
        for oneinterface in nicrec['interface']:
            tinterface = interface(oneinterface)
            self.interface.append(tinterface)
