import ipaddress

from .nic import Nic
from . import session

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