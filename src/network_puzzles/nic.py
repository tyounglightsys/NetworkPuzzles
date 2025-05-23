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

def beginIngress(packRec, nicRec):
    """Begin the packet entering a device.  It enters via a nic, and then is processed.
    Args: 
        packetRec: a packet record - the packet entering the device
        nicRec: a network card record - the nic on the device that we are entering.
    returns: nothing
    """
    #Notes from EduNetworkBuilder
    #Check to see if we have tests that break stuff.
    # - DeviceNicSprays (nic needs to be replaced)
    # - Device is frozen (packet is dropped)
    # - Device is burned (packet is dropped)
    # - Device is powered off (packet is dropped)
    #
    # - Check to see if we are firewalled.  Drop packet if needed
    # If none of the above...
    # if the packet is destined for this NIC/interface, then we accept and pass it to the device to see if we should respond
    # If the packet is a broadcast, check to see if we should respond
    # - We might both route it and respond to a broadcast (broadcast ping and switch responds)
    # If we route packets, accept it for routing.
    # 