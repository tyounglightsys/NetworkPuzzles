import ipaddress

from .nic import Nic
from . import session
from . import packet

class Device:
    #define things by their type for later use in intellisense
    hostname: str
    size: int #a size.  100 or something like that
    uniqueidentifier: str
    location: str #This should be a point, x,y

    def __init__(self, devicerec):
        #define the varables as specific types so intellisense works nicely with it
        self.hostname = devicerec['hostname']
        self.size = int(devicerec['size'])
        self.uniqueidentifier = devicerec['uniqueidentifier']
        self.location = devicerec['location']
        self.mtype = devicerec['mytype']
        self.isdns = devicerec['isdns']
        self.isdhcp = devicerec['isdhcp']
        self.nic = []
        if not isinstance(devicerec['nic'], list):
            devicerec['nic'] = [ devicerec['nic'] ] #turn it into a list if it was not one before
        for onenic in devicerec['nic']:
            #loop through them and add them separately
            tnic = Nic(onenic)
            self.nic.append(tnic)

def forwardsPackets(deviceRec):
    """return true if the device does packet forwarding (switch/hub/etc), false if it does not"""
    match deviceRec['mytype']:
        case "net_switch","net_hub","wap","wbridge","wrepeater","wrouter":
            return True
    return False

def routesPackets(deviceRec):
    """return true if the device routes packets, false if it does not"""
    match deviceRec['mytype']:
        case "router","firewall":
            return True
    return False

def doesVLANs(deviceRec):
    """return true if the device does vlans, false if it does not"""
    match deviceRec['mytype']:
        case "net_switch","firewall","router":
            return True
    return False

def isWirelessForwarder(deviceRec):
    """return true if the device is a wireless device that does forwarding, false if it does not"""
    match deviceRec['mytype']:
        case "wrepeater","wap","wbridge","wrouter":
            return True
    return False

def nicFromName(theDevice,what):
    """return the network card from the name
    Args:
        theDevice:str - the hostname of the device that contains the nic we are looking for
        theDevice:device - the device containing the nic we are looking for
        what:str - the network card name we are looking for
    Returns:
        the network card record from the device or None
        """
    if isinstance(theDevice, str):
        theDevice = deviceFromName(theDevice)
    if theDevice is None:
        return None
    for one in theDevice['nic']:
        if one['nicname'] == what:
            return one
    return None

def nicFromID(what):
    """find the network card from the id
    Args: what:int - the device id for the nic you are looking for
    Notes:
        Each component on the network has a unique ID.  PCs can change names, so we do not assume host-names are unique.
        Thus, for a network link (ethernet cable, wireless, etc) to know what two devices it is connecting, we use the ID
    """
    for theDevice in allDevices():
        for one in theDevice['nic']:
            if one['uniqueidentifier'] == what:
                return one
    return None

def deviceFromName(what):
    """Return the device, given a name
    Args: what:str the hostname of the device
    returns the device matching the name, or None"""
    return device.deviceFromName(what)

def deviceFromID(what):
    """Return the device, given a name
    Args: what:int the unique id of the device
    returns the device matching the id, or None"""
    return device.deviceFromID(what)

def linkFromName(what):
    """
    Return the link matching the name
    Args: what:str - the string name of the link
    returns: the link record or None
    """
    for one in allLinks():
        if one['hostname'] == what:
            return one
    return None

def linkFromDevices(srcDevice, dstDevice):
    """return a link given the two devices at either end
    Args:
        srcDevice:Device - the device itself
        srcDevice:str - the hostname of the device
        dstDevice:device - the device itself
        dstDevice:str - the hostname of the device
    Returns: a link record or None
    """
    srcstr=""
    dststr=""
    if isinstance(srcDevice,str):
        srcstr=srcDevice
    else:
        if 'hostname' in srcDevice:
            srcstr=srcDevice['hostname']
    if isinstance(dstDevice,str):
        dststr=dstDevice
    else:
        if 'hostname' in dstDevice:
            dststr=dstDevice['hostname']
    #Now we should have srcstr and dststr set.  Use them to concoct a link name
    #The link name looks like: pc0_link_pc1
    result = linkFromName(srcstr + "_link_" + dststr)
    if result is not None:
        return result
    result = linkFromName(dststr + "_link_" + srcstr)
    if result is not None:
        return result
    #if we get here, we could not find it.  Return none
    return None

def allLinks():
    """
    Return a list that contains all devices in the puzzle.
    """
    # global puzzle
    linklist=[]
    if 'link' not in session.puzzle:
        session.puzzle['link'] = []
    for one in session.puzzle['link']:
        if 'hostname' in one:
            linklist.append(one)
    return linklist

def getInterfaceFromLinkNicRec(tLinkNicRec):
    """
    return the interface that the link connects to
    Args: 
    tLinkNicRec:link-Nic-rec.  This should be link['SrcNic'] or link['DstNic']
    returns: the interface record or None
    """
    #a nic rec looks like: { "hostid": "100", "nicid": "102", "hostname": "pc0", "nicname": "eth0" }
    tNic = nicFromID(tLinkNicRec['nicid'])
    if tNic is None:
        return None
    #If we get here, we have the nic record.
    return tNic

def linkFromID(what):
    """
    Return the link matching the id
    Args: what:int - the unique id of the link
    Returns: the matching link record or None
    """
    for one in allLinks():
        print(one['uniqueidentifier'])
        if one['uniqueidentifier'] == what:
            return one
    return None

def itemFromID(what):
    """return the item matching the ID.  Could be a device, a link, or a nic"""
    result = deviceFromID(what)
    if result is not None:
        return result
    result = linkFromID(what)
    if result is not None:
        return result
    result = nicFromID(what)
    if result is not None:
        return result
    return None


def allDevices():
    """
    Return a list that contains all devices in the puzzle.
    """
    devicelist=[]
    if 'device' not in session.puzzle:
        session.puzzle['device'] = []
    for one in session.puzzle['device']:
        if 'hostname' in one:
            devicelist.append(one)
    return devicelist

def deviceFromName(what):
    """Return the device, given a name
    Args: what:str the hostname of the device
    returns the device matching the name, or None"""
    for one in allDevices():
        if one['hostname'] == what:
            return one
    return None

def deviceFromID(what):
    """Return the device, given a name
    Args: what:int the unique id of the device
    returns the device matching the id, or None"""
    for one in allDevices():
        if one['uniqueidentifier'] == what:
            return one
    return None

def deviceCaptions(deviceRec, howmuch:str):
    """
    return a list of strings, giving information about this device.
    Args: 
        deviceRec - a device record.  pc0, laptop0, etc.
        howmuch:str - one of: 'none', 'full', 'host','host_ip','ip'
    returns an array of strings to be printed next to each device
    """
    captionstrings=[]
    match howmuch:
        #case 'none':
        #
        case 'full':
            captionstrings.append(deviceRec['hostname'])
            captionstrings.append(allIPStrings(deviceRec),True,True)
        case 'host':
            captionstrings.append(deviceRec['hostname'])
        case 'host_ip':
            captionstrings.append(deviceRec['hostname'])
            captionstrings.append(allIPStrings(deviceRec))
        case 'ip':
            captionstrings.append(allIPStrings(deviceRec))
    return captionstrings


def DeviceIPs(src, ignoreLoopback=True):
    """
    Return a list of all the ip addresses (IP+subnet) the device has.
    Args: 
        src:str - the hostname of the device
        src:device - the device record itself
        ignoreLoopback:bool=True - whether to ignore the loopback
    Returns:
        A list of IP4Interface records (ip+mask)
    """
    interfacelist=[]
    srcDevice=src
    if 'hostname' not in src:
        srcDevice=deviceFromName(src)
    if srcDevice is None:
        print('Error: passed in an invalid source to function: sourceIP')
        return None
    if not isinstance(srcDevice['nic'],list):
        #If it is not a list, turn it into a list so we can iterate it
        srcDevice['nic'] = [srcDevice['nic']]
    for onenic in srcDevice['nic']:
        #Pull out all the nic interfaces
        if not isinstance(onenic['interface'],list):
            #turn it into a list so we can iterate it
            onenic['interface']=[onenic['interface']]
        for oneinterface in onenic['interface']:
            #add it to the list
            if oneinterface['nicname'] == "lo0" and ignoreLoopback:
                #skip this interface if we are told to do so
                continue
            #print("Making list of ips:" + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            interfacelist.append(ipaddress.IPv4Interface(oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask']))
    return interfacelist

def allIPStrings(src, ignoreLoopback=True, appendInterfacNames=False):
    """
    Return a list of all the ip addresses (IP+subnet) the device has.
    Args: 
        src:str - the hostname of the device
        src:device - the device record itself
        ignoreLoopback:bool=True - whether to ignore the loopback
    Returns:
        A list of strings (ip+mask)
    """
    interfacelist=[]
    srcDevice=src
    if 'hostname' not in src:
        srcDevice=deviceFromName(src)
    if srcDevice is None:
        print('Error: passed in an invalid source to function: sourceIP')
        return None
    if not isinstance(srcDevice['nic'],list):
        #If it is not a list, turn it into a list so we can iterate it
        srcDevice['nic'] = [srcDevice['nic']]
    for onenic in srcDevice['nic']:
        #Pull out all the nic interfaces
        if not isinstance(onenic['interface'],list):
            #turn it into a list so we can iterate it
            onenic['interface']=[onenic['interface']]
        for oneinterface in onenic['interface']:
            #add it to the list
            if oneinterface['nicname'] == "lo0" and ignoreLoopback:
                #skip this interface if we are told to do so
                continue
            #print("Making list of ips:" + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            if appendInterfacNames:
                interfacelist.append(oneinterface['nicname'] + " " + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            else:
                interfacelist.append(oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
    return interfacelist

def beginIngressOnNIC(packRec, nicRec):
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
    nictype = nicRec['nictype'][0]
    #in certain cases we track inbound traffic; remembering where it came from.
    trackPackets = False
    theDevice = deviceFromName(nicRec['myid']['hostname'])
    #if it is a port (swicth/hub) or wport (wireless devices)
    if nictype == "port" or nictype == "wport":
        trackPackets = True
    if isWirelessForwarder(theDevice) and nictype == "wlan":
        trackPackets = True
    if nictype == "port" and theDevice['mytype'] == "wap":
        trackPackets = True
    if trackPackets:
        #We need to track ARP.  Saying, this MAC address is on this port. Simulates STP (Spanning Tree Protocol)
        1 #do nothing for now.  We will come back when we know how we want these stored
        #here we would store the MAC and tie it to this NIC.

    #If we are entering a WAN port, see if we should be blocked or if it is a return packet
    if nictype == "wan":
        1
        #We do not have the firewall programed in yet.
    
    if packRec['destMAC'] == nicRec['Mac'] or packet.isBroadcastMAC(packRec['destMac']) or nictype == "port" or nictype == "wport":
        #The packet is good, and has reached the computer.  Pass it on to the device
        1
        #Since we know the device, beginIngres on the device.
    else:
        packet['status'] = "dropped"