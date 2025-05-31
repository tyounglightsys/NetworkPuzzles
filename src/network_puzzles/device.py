import ipaddress
import copy
import random

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

def powerOff(deviceRec):
    """return true if the device is powered off"""
    if 'poweroff' not in deviceRec:
        return False
    try:
        match deviceRec['poweroff']:
            case "True":
                return True
    except ValueError:
        return False
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

def linkConnectedToNic(nicRec):
    """Find a link connected to the specified network card"""
    if nicRec is None:
        return None
    for one in allLinks():
        if(one['SrcNic']['nicid'] == nicRec['myid']['nicid'] ):
            return one
        if(one['DstNic']['nicid'] == nicRec['myid']['nicid'] ):
            return one
    #we did not find anything that matched.  Return None
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

def getDeviceNicFromLinkNicRec(tLinkNicRec):
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

def routeRecFromDestIP(theDeviceRec,destinationIPString:str):
    """return a routing record given a destination IP string.  The device record has the route, nic, interface, and gateway"""
    #go through the device routes.
    routeRec = {}
    if  'route' not in theDeviceRec:
        theDeviceRec['route'] = []
    if not isinstance(theDeviceRec['route'], list):
        theDeviceRec['route'] =  [ theDeviceRec['route']] #turn it into a list
    for oneroute in theDeviceRec['route']:
        staticroute=ipaddress.ip_network(oneroute['ip' + "/" + oneroute['mask']])
        if destinationIPString in staticroute:
            #We found a gateway that we should use.
            routeRec['gateway'] = oneroute['gateway'] #just the gateway
            break

    #if not a device route, look through nics
    if 'gateway' not in routeRec:
        #We did not find it in the static routes.  Loop through all nics and see if one is local
        for oneNic in theDeviceRec['nic']:
            localInterface = findLocalNICInterface(destinationIPString,oneNic)
            if localInterface is not None:
                #We found it.  Use it.
                routeRec['nic'] = oneNic
                routeRec['interface'] = localInterface
                break

    #if not a nic, use the default gateway
    if 'gateway' not in routeRec and 'nic' not in routeRec:
        #use the device default gateway
        routeRec['gateway'] = theDeviceRec['gateway']['ip']
    
    #if we have a gateway but do not know the nic and interface, find the right one
    if 'gateway' in routeRec and 'nic' not in routeRec:
        for oneNic in theDeviceRec['nic']:
            localInterface = findLocalNICInterface(routeRec['gateway'],oneNic)
            if localInterface is not None:
                #We found it.  Use it.
                routeRec['nic'] = oneNic
                routeRec['interface'] = localInterface
                break
    
    #We should now have a good routeRec.  gateway might be blank, if it is local
    #But we should have a nic and interface set
    if 'interface' not in routeRec:
        #We could not figure out the route.  return None.
        return None
    return routeRec

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

def interfaceIP(interfaceRec):
    """pull out the interface IP address for the specified interface.  Put it into a function so we can make it work for IPv4 and IPv6"""
    return interfaceRec['myip']['ip']+"/" + interfaceRec['myip']['mask']

def findLocalNICInterface(targetIPstring:str, networkCardRec):
    """Return the network interface record that has an IP address that is local to the IP specified as the target
    Args: 
        targetIPstring:str - a string IP address, which we are trying to find a local interface for
        networCardRec:nicRecord - a netetwork card record, which may contain multiple interfaces
    returns: the interface record that is local to the target IP, or None"""
    if networkCardRec is None:
        return None
    if networkCardRec['nictype'][0] == 'port':
        return None #Ports have no IP address
    #loop through all the interfaces and return any that might be local.
    if not isinstance(networkCardRec['interface'],list):
        networkCardRec['interface'] = [ networkCardRec['interface']] #turn it into a list if needed.
    for oneIF in networkCardRec['interface']:
        if packet.isLocal(targetIPstring, interfaceIP(oneIF)):
            return oneIF
    return None

def findPrimaryNICInterface(networkCardRec):
    """return the primary nic interface.  Turns out this is always interface 0"""
    if len(networkCardRec['nictype']) > 0:
        return networkCardRec['nictype'][0]
    return None

def doInputFromLink(packRec, nicRec):
    #figure out what device belongs to the nic
    thisDevice = deviceFromID(nicRec['myid']['hostid'])

    #Do the simple stuff
    if powerOff(thisDevice):
        packRec['status'] = "done"
        #nothing more to be done
        return False
    #If the packet is a DHCP answer, process that here.  To be done later
    #If the packet is a DHCP request, and this is a DHCP server, process that.  To be done later.

    #Find the network interface.  It might be none if the IP does not match, or if it is a switch/hub device.
    tInterface = findLocalNICInterface(packRec['tdestIP'], nicRec)
    #if this is None, try the primary interface.
    if tInterface is None:
        tInterface = findPrimaryNICInterface(nicRec)
    #the interface still might be none if we are a switch/hub port
    #Verify the interface.  This is mainly to work with SSIDs, VLANs, VPNs, etc.
    if tInterface is not None:
        beginIngressOnInterface(packRec, tInterface)

    #the packet status should show dropped or something if we have a problem. 
    #but for now, pass it onto the NIC
    return beginIngressOnNIC(packRec, nicRec)
    #The NIC passes it onto the device if needed.  We are done with this.


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
        #if the packet is a return ping packet, allow it. Otherwise, reject
    
    if packRec['destMAC'] == nicRec['Mac'] or packet.isBroadcastMAC(packRec['destMAC']) or nictype == "port" or nictype == "wport":
        #The packet is good, and has reached the computer.  Pass it on to the device
        return packetEntersDevice(packRec, theDevice, nicRec)
    else:
        packRec['status'] = "dropped"
        return False

def beginIngressOnInterface(packRec, interfaceRec):
    """Here we would do anything needed to be done with the interface.
        VLAN
        SSID
        Tunnel/VPN
        """
    #right now, we let pass it back
    return True

def packetEntersDevice(packRec, thisDevice, nicRec):
    """When a packet enters a device, coming from an interface and network card.  Here we respond to stuff, route, or switch..."""
    if powerOff(thisDevice):
        packRec['status'] = "done"
        #nothing more to be done
        return False
    #We would check if it was frozen.  That is a test, not a status.  We do not have that check yet.

    #Deal with DHCP.  If it is an answer, update the device IP address.
    #If it is a request and this is a DHCP server, serve an IP back.

    #If the packet is destined for here, process that
    # ping, send ping packet back
    # ping response, mark it as done

    #If the packet is not done and we forward, forward. Basically, a switch/hub
    if packRec['status'] != 'done' and forwardsPackets(thisDevice):
        #We loop through all nics. (minus the one we came in from)
        for onenic in thisDevice['nic']:
            #we duplicate the packet and send it out each port-type
            #find the link connected to the port
            tlink = linkConnectedToNic(nicRec)
            if tlink is not None and nicRec['uniqueidentifier'] != onenic['uniqueidentifier']:
                #We have a network wire connected to the NIC.  Send the packet out
                #if it is a switch-port, then we check first if we know where the packet goes - undone
                tpacket = copy.deepcopy(packRec)
                tpacket['packetlocation'] = tlink['hostname']
                if tlink['SrcNic']['nicid'] == onenic['SrcNic']['nicid']:
                    tpacket['packetDirection'] = 1 #Src to Dest
                else:
                    tpacket['packetDirection'] = 2 #Dest to Source
                tpacket['packetDistance'] = 0 #start at the beginning.
                packet.addPacketToPacketlist(tpacket)
                print (" Sending packet out a port: " + tpacket['packetlocation']) 
        #we set this packet as done.
        packRec['status'] = 'done' #The packet that came in gets killed since it was replicated everywhere else
    #if the packet is not done and we route, route
    if packRec['status'] != 'done' and routesPackets(thisDevice):
        sendPacketOutDevice(packRec,thisDevice)

def AssignMacIfNeeded(nicRec):
    if 'Mac' not in nicRec:
        #Most of the network cards do not have this done yet.  We generate a new random one
        localmac=""
        for i in range(1,13):
            localmac=localmac+random.choice("ABCDEF1234567890")
        nicRec['Mac']=localmac

def sendPacketOutDevice(packRec, theDevice):
    """Send the packet out of the device."""
    print("Sending packet out a device: " + theDevice['hostname'])
    #determine which interface/nic we are exiting out of - routing
    routeRec = routeRecFromDestIP(theDevice,packRec['destIP'])
    #set the source MAC address on the packet as from the nic
    if routeRec is not None:
        AssignMacIfNeeded(routeRec['nic'])
        packRec['sourceMAC'] = routeRec['nic']['Mac']
    #set the destination MAC to be the GW MAC if the destination is not local
        #this needs an ARP lookup.  That currently is in puzzle, which would make a circular include.

    #set the packet location being the link associated with the nic
    #   Fail if there is no link on the port
    destlink = linkConnectedToNic(routeRec['nic'])
    if destlink is not None:
        packRec['packetlocation'] = destlink['hostname']
        if destlink['SrcNic']['hostname'] == theDevice['hostname']:
            packRec['packetDirection'] = 1 #Src to Dest
        else:
            packRec['packetDirection'] = 2 #Dest to Source
        return True
    #If we get here, it did not work.  No route to host.
    #right now, we blow up.  We need to deal with this with a bit more grace.  Passing the error back to the user
    packRec['status'] = 'failed'
    raise Exception("No Route to host")
