import copy
from . import puzzle

class Link:
    def __init__(self, linkrec):
        self.hostname = linkrec['hostname']
        self.linktype = linkrec['linktype']
        self.uniqueidentifier = linkrec['uniqueidentifier']
        self.SrcNic = copy.copy(linkrec['SrcNic'])
        self.DstNic = copy.copy(linkrec['DstNic'])

def getInterfaceFromLinkNicRec(tLinkNicRec):
    """
    return the interface that the link connects to
    Args: 
    tLinkNicRec:link-Nic-rec.  This should be link['SrcNic'] or link['DstNic']
    returns: the interface record or None
    """
    #a nic rec looks like: { "hostid": "100", "nicid": "102", "hostname": "pc0", "nicname": "eth0" }
    tNic=puzzle.nicFromID(tLinkNicRec['nicid'])
    if tNic is None:
        return None
    #If we get here, we have the nic record.
    return tNic