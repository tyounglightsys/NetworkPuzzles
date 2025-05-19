#!/usr/bin/python3
#All the functions needed for reading the EduNetwork Puzzle file
#And getting information from it
import ipaddress
import json
import copy
import random
import re
import os

# define the global network list
from . import session


def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The JSON data as a Python dictionary, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {file_path}")
        return None

def listPuzzles(regex_pattern:str = None):
    puzzleNames=[]
    directory_path="src/network_puzzles/resources/puzzles"
    list = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    for one in list:
        justName=re.sub(r"\.json","", one)
        if regex_pattern is None:
            puzzleNames.append(justName)
        elif re.match(regex_pattern,justName):
            puzzleNames.append(justName)
    return puzzleNames

def readPuzzle():
    """Read in the puzzles from the various .json files"""
    if len(session.puzzlelist) == 0:
        allfiles=listPuzzles("Level.*")
        for one in allfiles:
            #We stripped off the ".json" from the name, so we need to add it back
            file_path = 'src/network_puzzles/resources/puzzles/' + one + ".json"
            oneentry =read_json_file(file_path)
            oneentry['EduNetworkBuilder']['Network']['name'] = one
            session.puzzlelist.append(oneentry)
            #print("loading: " + one)

def choosePuzzleFromName(what:str):
    """
    Choose a puzzle using the puzzle name.
    Args: 
        what: string - The puzzle name, matching case and everything, of the puzzle we want to select
    """
    readPuzzle()
    #print ("Length of puzzleslist: " + str(len(puzzlelist)))

    for one in session.puzzlelist:
        if one['EduNetworkBuilder']['Network']['name'] == what:
            return copy.deepcopy(one['EduNetworkBuilder']['Network'])

def choosePuzzle(what, filter=None):
    """
    Choose a puzzle from the list of available puzzles.
    Args: 
        what: int - the index of the puzzle we want to select
        what: str - use choosePuzzleFromName
        filter: str - this is a filter to use.  For example ".*DHCP.*".  Then the int would apply to the index in the filtered list
    """
    readPuzzle()
    myint=1
    if filter is not None:
        #We have a filter.  We need to try to look up the item from the filtered list
        filteredList=listPuzzles(filter)
        if len(filteredList) > 0:
            #this means it is a valid filter. Try to use it.
            try:
                what = filteredList[int(what)]
            except Exception:
                #It did not work.  Ignore the filter.
                myint=1

    if isinstance(what,int):
       puz = copy.deepcopy(session.puzzlelist[what]['EduNetworkBuilder']['Network'])
    else:
        try:
            #if the int(what) fails, we treat it as a name
            puz = copy.deepcopy(session.puzzlelist[int(what)]['EduNetworkBuilder']['Network'])
        except Exception:
            puz = choosePuzzleFromName(what)
    if puz is not None:
        print("Loaded: " + puz['name'])
    return puz

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


def maclistFromDevice(src):
    """
    Return a list of all the MAC addresses of all the nics on the device
    Args:
        src:str - lookup the source device using the hostname and return all MAC addresses
        src:device - lookup all the MAC addresses in this device

    Returns:
        A list of mac-addresses.  Each MAC is a struct containing at least the ip and mac.
    """
    maclist=[]
    if isinstance(src,str):
        src = deviceFromName(str)
    if src == None:
        return None
    if not 'nic' in src:
        return None
    if not isinstance(src['nic'],list):
        src['nic'] = [src['nic']]
    for onenic in src['nic']:
        #iterate through the list of nics
        if not 'Mac' in onenic:
            #Most of the network cards do not have this done yet.  We generate a new random one
            localmac=""
            for i in range(1,13):
                localmac=localmac+random.choice("ABCDEF1234567890")
            onenic['Mac']=localmac
        if not onenic['nicname'] == 'lo0':
            if not isinstance(onenic['interface'],list):
                onenic['interface'] = [ onenic['interface']]
            for oneinterface in onenic['interface']:
                onemac = {
                    'ip':ipaddress.ip_interface(oneinterface['myip']['ip']+"/"+oneinterface['myip']['mask']),
                    'mac':onenic['Mac']
                }
            maclist.append(onemac)
    return maclist


def buildGlobalMACList():
    """Build/rebuild the global MAC list.  Should be run when we load a new puzzle, when we change IPs, or add/remove NICs."""
    # global maclist
    session.maclist = [] #clear it out
    for onedevice in allDevices():
        for onemac in maclistFromDevice(onedevice):
            session.maclist.append(onemac)
    #print("Built maclist")
    #print(maclist)
    return session.maclist

def justIP(ip):
    """return just the IP address as a string, stripping the subnet if there was one"""
    if not isinstance(ip,str):
        ip = str(ip) #change it to a string
    ip = re.sub("/.*","", ip)
    return ip 


def globalArpLookup(ip):
    """Look up an IP address in the global ARP database.
    Args:
        ip:str the IP address as a string.
        ip:ipaddress the IP as an ipaddress
    Returns:
        The MAC address corresponding to the IP as a string or None.
    """
    if not isinstance(session.maclist,list):
        buildGlobalMACList()
    print("we have maclist")
    print(session.maclist)
    if isinstance(ip,str):
        ip = ipaddress.IPv4Address(ip)
        print ("globalARP: Converting ip: " + str(ip))
    for oneMac in session.maclist:
        print ("globalARP: comparing: " + justIP(oneMac['ip']) + " to " + justIP(ip))
        if justIP(oneMac['ip']) == justIP(ip):
            return oneMac['mac']
    return None

def arpLookup(srcDevice, ip):
    """find a mac address, with the source being the specified device
    Args:
        srcDevice:str the hostname of the device we are looking at
        srcDevice:device the device record we are looking at
        ip:str the string ip address we are trying to find
        ip:ipaddress the ip address we are trying to find
        """
    oldsrc=""
    if srcDevice == None:
        print("Error: source to arpLookup is None")
    if isinstance(srcDevice, str):
        #We need to look the device up
        oldsrc = srcDevice
        srcDevice = deviceFromName(srcDevice)
    if srcDevice == None:
        print("Error: Unable to find source for arpLookup: " + oldsrc)
    #If we are here, src should be a valid device
    if isinstance(ip,str):
        ip = ipaddress.IPv4Address(ip)
        print ("ARP: Converting ip: " + justIP(ip))
    if 'maclist' not in srcDevice:
        srcDevice['maclist']=[] #make an empty list.  That way we can itterate through it
    #The maclist on a device should have the port on which the MAC is found.  Particularly on switches. 
    #Does the device arp list have any records?  If so, use that.
    for oneMAC in srcDevice['maclist']:
        #print ("ARP: comparing: " + justIP(oneMAC['ip']) + " to " + justIP(ip))
        if justIP(oneMAC['ip']) == justIP(ip):
            print("Found the MAC for IP " + justIP(ip))
            return oneMAC['mac'] #Return the one in the local arp.
    #If we cannot find it on the device, look it up from the global list
    tmac = globalArpLookup(ip)
    if tmac is not None:
        #Store the mac address in the local list
        arp = {
            'ip':ip,
            'mac':tmac
        }
        srcDevice['maclist'].append(arp)
        #we asked for the mac address corresponding to the IP.  Return just the MAC
        return tmac
    return None

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
    if theDevice == None:
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
    if result != None:
        return result
    result = linkFromName(dststr + "_link_" + srcstr)
    if result != None:
        return result
    #if we get here, we could not find it.  Return none
    return None

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
    if result != None:
        return result
    result = linkFromID(what)
    if result != None:
        return result
    result = nicFromID(what)
    if result != None:
        return result
    return None

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
    if not 'hostname' in src:
        srcDevice=deviceFromName(src)
    if srcDevice == None:
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
            if oneinterface['nicname'] == "lo0" and ignoreLoopback == True:
                #skip this interface if we are told to do so
                continue
            print("Making list of ips:" + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            interfacelist.append(ipaddress.IPv4Interface(oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask']))
    return interfacelist

def destIP(srcDevice,dstDevice):
    """
    Find the destination IP address of the specified device, if going there from the source device.
    Many devices have multiple IP addresses.  If the IP is local, we go straight to it.  If it is on
    a different subnet, we get routed there.  This is a poor-man's DNS.
    Args:
        srcDevice:str - the hostname of the source device
        srcDevice:device - the device record of the source
        dstDevice:str - the hostname of the destination device
        dstDevice:device - the device record of the destination
    Returns:
        the string IP address of the nic that is local betwee the two devices, or the IP address on the destination 
        that is connected to its gateway IP.  None if the IP cannot be determined 
    """
    if srcDevice == None:
        print("Error: function destIP: None passed in as source.")
        return None
    if dstDevice == None:
        print("Error: function destIP: None passed in as destination.")
        return None
    if not 'hostname' in srcDevice:
        print("Error: function destIP: Not a valid source device.")
        return None
    if not 'hostname' in dstDevice:
        print("Error: function destIP: Not a valid destination device.")
        return None
    srcIPs = DeviceIPs(srcDevice)
    dstIPs = DeviceIPs(dstDevice)

    if srcIPs == None or dstIPs == None:
        #we will not be able to find a match.
        return None
    for oneSip in srcIPs:
        for oneDip in dstIPs:
            #compare each of them to find one that is local
            if oneSip in oneDip.network:
                #We found a match.  We are looking for the destination.  So we return that
                return oneDip
    #if we get here, we did not find a match
    #we need to find the IP address that is local to the gateway and use that.
    return None

def sourceIP(src,dstIP):
    """
    Find the IP address to use when pinging the destination.  If the address is local, use the local nic.
    If the address is at a distance, we use the IP address associated with whatever route gets us there.
    Args:
        src:str - use the hostname as the source
        src:device - use src as the source device
        destIP:str - connect to this ip.  Eg: "192.168.1.1"
    return: an IP address string, or None
    """
    srcDevice=src
    if not 'hostname' in src:
        srcDevice=deviceFromName(src)
    if srcDevice == None:
        print('Error: passed in an invalid source to function: sourceIP')
        return None
    #Get all the IPs from this device
    allIPs = DeviceIPs(src)
    if allIPs == None:
        return None

    #return the IP that has a static route to it (add this later).
    if 'route' in srcDevice:
        if not isinstance(srcDevice['roiute'],list):
            srcDevice['route'] = [srcDevice['route']]
        for oneroute in srcDevice['route']:
            staticroute=ipaddress.ip_network(oneroute['ip' + "/" + oneroute['mask']])
            if dstIP in staticroute:
                #We found the route.  But we need to find the IP address that is local to the route
                print("A static route matched.  Finding the IP for that route")
                for oneip in allIPs:
                    #oneip=ipaddress.IPv4Interface
                    if oneip in staticroute:
                        print("We found a local interface that worked with the route")
                        print(oneip.ip)
                        return oneip
        
    #return the IP that is local to the dest IP
    for oneip in allIPs:
        #oneip=ipaddress.IPv4Interface
        if dstIP in oneip.network:
            print("We found a local network ")
            print(oneip.ip)
            return oneip
    #if we get here, we do not have a nic that is local to the destination.  Return the nic that the GW is on
    GW = ipaddress.ip_address(srcDevice['gateway']['ip'] + "/" + srcDevice['gateway']['netmask'])
    for oneip in allIPs:
        if GW in oneip.ip_network:
            print("The gateway is the way forward ")
            print(oneip.ip)
            return oneip

    #if we do not have a GW, we need to report, "no route to host"
    print ("no path")
    return None

def is_ipv4(string):
        """
        return True if the string is a valid IPv4 address.
        """
        try:
            ipaddress.IPv4Network(string)
            return True
        except ValueError:
            return False

def Ping(src, dest):
    #src should be a device, not just a name.  Sanity check.
    if not 'hostname' in src:
        #The function is being improperly used. Can we fix it?
        newsrc = deviceFromName(src)
        if newsrc != None:
            src=newsrc
        else:
            #we were unable to fix it.  Complain bitterly
            print('Error: invalid source passed to ping function.  src must be a device.')
            return None
    if src == None:
        #the function is being improperly used
        print('Error: ping function must have a valid device as src.  None was passed in.')
        return None
    #dest should be a device, an ip address, or a hostname
    if dest == None:
        print('Error: You must have a destination for ping.  None was passed in.')
        return None
    if isinstance(dest,str) and not is_ipv4(dest):
        #If it is a string, but not a string that is an IP address
        dest = deviceFromName(dest)
    if 'hostname' in dest:
        #If we passed in a device or hostname, convert it to an IP
        dest = destIP(src,dest)
    if dest == None:
        #This means we were unable to figure out the dest.  No such host, or something
        print('Error: Not a valid ping target')
        return None
    if isinstance(dest,ipaddress.IPv4Address):
        #This is what we are hoping for.
        packet=newPacket() #make an empty packet
        packet['sourceIP'] = sourceIP(src, dest)
        #packet['sourceMAC'] = #the MAC address of the above IP
        packet['sourceMAC'] = arpLookup(src,packet['sourceIP'])
        #packet['destIP'] = #figure this out
        packet['destIP'] = dest #this should now be the IP
        #packet['destMAC'] = #If the IP is local, we use the MAC of the host.  Otherwise it is the MAC of the gateway
        packet['destMAC'] = globalArpLookup(dest)
        packet['packettype']="ping"
        print (packet)

def newPacket():
    packet={
        'packetype':"",
        'VLANID':0, #start on the default vlan
        'health':100, #health.  This will drop as the packet goes too close to things causing interferance
        'sourceIP':"",
        'destIP':"",
        'sourceMAC':"",
        'destMAC':"",
        'payload':"",
        'packetDirection':0 #Which direction are we going on a network link.  1=src to dest, 2=dest to src
    }
    return packet

def doTest():

    #mynet=choosePuzzlek('Level0-NeedsLink')
    mynet=choosePuzzle(3)
    print (mynet['name'])
    mydevice=deviceFromID('110');
    #print(mydevice)
    #mynic=nicFromName(mydevice,'eth0')
    mynic=nicFromID('112')
    #print(mynic)
    mylink=linkFromID('121')
    print(mylink)
