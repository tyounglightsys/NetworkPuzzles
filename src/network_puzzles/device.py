import ipaddress
import copy
import logging

from .nic import Nic
from . import session
from . import packet


class Device:
    def __init__(self, value=None):
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        if isinstance(value, int):
            self.json = session.puzzle.device_from_uid(value)
        # define the varables as specific types so intellisense works nicely with it
        elif isinstance(value, str):
            # Find device by hostname.
            self.json = session.puzzle.device_from_name(value)
        elif isinstance(value, dict):
            self.json = value
        else:
            raise ValueError(
                f"Not a valid uniqueidentifier, hostname, or JSON data: {value}"
            )
        if self.json is None:
            self.json = {}

    @property
    def hostname(self):
        return self.json.get("hostname")

    @hostname.setter
    def hostname(self, name):
        self.json["hostname"] = name

    @property
    def is_dhcp(self):
        if self.json.get("isdhcp", "").lower() in ("true", "yes"):
            value = True
        else:
            value = False
        logging.debug(f"{self.hostname}.is_dhcp {value=}")
        return value

    @is_dhcp.setter
    def is_dhcp(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["isdhcp"] = value

    @property
    def is_invisible(self):
        if self.json.get("isinvisible", "").lower() in ("true", "yes"):
            # The device is hidden.
            value = True
        else:
            value = False
        # logging.debug(f"{self.hostname}.is_invisible: {value} ")
        return value

    @is_invisible.setter
    def is_invisible(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["isinvisible"] = value

    @property
    def location(self):
        loc = self.json.get("location")
        if loc:
            location = loc.split(",")
            location = (int(location[0]), int(location[1]))
            logging.debug(f"{self.hostname} {location=}")
            return location
        raise ValueError(f"Invalid JSON location data for '{self.hostname}'")

    @property
    def powered_on(self):
        if self.json.get("poweroff", "").lower() in ("true", "yes"):
            value = False
        else:
            value = True
        # logging.debug(f"{self.hostname}.powered_on: {value}")
        return value

    @powered_on.setter
    def powered_on(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["poweroff"] = value

    @property
    def blown_up(self):
        value = False
        if 'blownup' in self.json:
            if self.json.get("blownup", "").lower() in ("true", "yes"):
                value = True
            else:
                value = False
            # logging.debug(f"{self.hostname}.powered_on: {value}")
        session.print(f"Checking blown up state of {self.hostname} and found it to be {value}")
        return value

    @blown_up.setter
    def blown_up(self, value):
        #we can only set it to true.  We cannot unset this value.
        #to make it 'false', we need to replace the device
        if (isinstance(value,bool) and value) or (isinstance(value,str) and value.lower() == 'true'): 
            if isinstance(value, bool):
                value = str(value)
            self.json["blownup"] = value
            self.powered_on = True #when it blows up, the power gets turned off

    @property
    def uniqueidentifier(self):
        return self.json.get("uniqueidentifier")

    def all_nics(self):
        if not isinstance(self.json.get("nic"), list):
            self.json["nic"] = [self.json["nic"]]
        return self.json.get("nic")

    def all_tests(self):
        tests = []
        for t in session.puzzle.all_tests():
            if t.get("shost") == self.hostname:
                tests.append(t)
        return tests

    def get_nontest_commands(self):
        # Add item-related commands for items not mentioned in tests.
        commands = list()
        if not self.powered_on:
            commands.append(f"set {self.hostname} power on")
        return commands

    def mac_list(self):
        """
        Return a list of all the MAC addresses of all the nics on the device
        Args:
            name: str - define the device using the given hostname

        Returns:
            A list of mac-addresses.  Each MAC is a struct containing at least the ip and mac.
        """
        maclist = []
        if "nic" not in self.json:
            return None
        if not isinstance(self.json.get("nic"), list):
            self.json["nic"] = [self.json.get("nic")]
        for onenic in self.json.get("nic"):
            # iterate through the list of nics
            onenic = Nic(onenic).ensure_mac()
            if not onenic.get("nicname") == "lo0":
                if not isinstance(onenic.get("interface"), list):
                    onenic["interface"] = [onenic.get("interface")]
                for oneinterface in onenic.get("interface"):
                    onemac = {
                        "ip": ipaddress.ip_interface(
                            oneinterface["myip"]["ip"]
                            + "/"
                            + oneinterface["myip"]["mask"]
                        ),
                        "mac": onenic["Mac"],
                    }
                maclist.append(onemac)
        return maclist

    def nic_from_name(self, nicname):
        """return the network card from the name
        Args:
            name: str - the hostname of the device that contains the nic we are looking for
            theDevice:device - the device containing the nic we are looking for
            what:str - the network card name we are looking for
        Returns:
            the network card record from the device or None
        """
        if "nic" not in self.json:
            return None
        return self._item_by_attrib(self.json.get("nic"), "nicname", nicname)

    def interface_from_name(self, interfacename):
        """return the network interface from the name
        Args:
        Returns:
            the network interface record from the device or None
        """
        if "nic" not in self.json:
            return None
        if not isinstance(self.json["nic"], list):
            self.json["nic"] = [self.json["nic"]]
        for onenic in self.json["nic"]:
            if not isinstance(onenic["interface"], list):
                onenic["interface"] = [onenic["interface"]]
            for oneinterface in onenic["interface"]:
                if oneinterface.get("nicname") == interfacename:
                    return oneinterface
        return None

    def _item_by_attrib(self, items: list, attrib: str, value: str) -> dict | None:
        # Returns first match; i.e. assumes only one item in list matches given
        # attribute. It also assumes that 'items' is a list of dicts or json data.
        for item in items:
            if item.get(attrib) == value:
                return item


def buildGlobalMACList():
    """Build/rebuild the global MAC list.  Should be run when we load a new puzzle, when we change IPs, or add/remove NICs."""
    # global maclist
    session.maclist = []  # clear it out
    for onedevice in session.puzzle.devices:
        if onedevice:
            # print ("finding macs for " + onedevice['hostname'])
            # for onemac in maclistFromDevice(onedevice):
            for onemac in Device(onedevice).mac_list():
                session.maclist.append(onemac)
    # print("Built maclist")
    # print(maclist)
    return session.maclist


def globalArpLookup(ip):
    """Look up an IP address in the global ARP database.
    Args:
        ip:str the IP address as a string.
        ip:ipaddress the IP as an ipaddress
    Returns:
        The MAC address corresponding to the IP as a string or None.
    """
    # print ("doing global ARP lookup for ")
    # print (ip)
    # if not isinstance(session.maclist,list):
    buildGlobalMACList()
    # print("we have maclist")
    # print(session.maclist)
    if isinstance(ip, str):
        if ip == "0.0.0.0":
            return None # Never find a mac for this.  Possible many devices would match and it it not a valid IP
        ip = ipaddress.IPv4Address(ip)
        # print ("globalARP: Converting ip: " + str(ip))
    else:
        if packet.isEmpty(str(ip)):
            return None # Never find a mac for this.  Possible many devices would match and it it not a valid IP
    for oneMac in session.maclist:
        # print ("globalARP: comparing: " + packet.justIP(oneMac['ip']) + " to " + packet.justIP(ip))
        if packet.justIP(oneMac["ip"]) == packet.justIP(ip):
            return oneMac["mac"]
    return None


def arpLookup(srcDevice, ip):
    """find a mac address, with the source being the specified device
    Args:
        srcDevice:str the hostname of the device we are looking at
        srcDevice:device the device record we are looking at
        ip:str the string ip address we are trying to find
        ip:ipaddress the ip address we are trying to find
    """
    oldsrc = ""
    if srcDevice is None:
        logging.error("Error: source to arpLookup is None")
    if isinstance(srcDevice, str):
        # We need to look the device up
        oldsrc = srcDevice
        srcDevice = session.puzzle.device_from_name(srcDevice)
    if srcDevice is None:
        logging.error("Error: Unable to find source for arpLookup: " + oldsrc)
    # If we are here, src should be a valid device
    if isinstance(ip, str):
        if ip == "0.0.0.0":
            return None #Never find a destination for this one
        ip = ipaddress.IPv4Address(ip)
        logging.info("ARP: Converting ip: " + packet.justIP(ip))
    if "maclist" not in srcDevice:
        srcDevice[
            "maclist"
        ] = []  # make an empty list.  That way we can itterate through it
    # The maclist on a device should have the port on which the MAC is found.  Particularly on switches.
    # Does the device arp list have any records?  If so, use that.
    for oneMAC in srcDevice["maclist"]:
        # print ("ARP: comparing: " + justIP(oneMAC['ip']) + " to " + justIP(ip))
        if packet.justIP(oneMAC["ip"]) == packet.justIP(ip):
            logging.info("Found the MAC for IP " + packet.justIP(ip))
            return oneMAC["mac"]  # Return the one in the local arp.
    # If we cannot find it on the device, look it up from the global list
    tmac = globalArpLookup(ip)
    if tmac is not None:
        # Store the mac address in the local list
        arp = {"ip": ip, "mac": tmac}
        srcDevice["maclist"].append(arp)
        # we asked for the mac address corresponding to the IP.  Return just the MAC
        return tmac
    return None


def forwardsPackets(deviceRec):
    """return true if the device does packet forwarding (switch/hub/etc), false if it does not"""
    match deviceRec["mytype"]:
        case "net_switch" | "net_hub" | "wap" | "wbridge" | "wrepeater" | "wrouter":
            return True
    return False


def routesPackets(deviceRec):
    """return true if the device routes packets, false if it does not"""
    match deviceRec["mytype"]:
        case "router" | "firewall":
            return True
    return False


def doesVLANs(deviceRec):
    """return true if the device does vlans, false if it does not"""
    match deviceRec["mytype"]:
        case "net_switch" | "firewall" | "router":
            return True
    return False


def servesDHCP(deviceRec):
    """return true if the device can serve dhcp, false if it can not"""
    match deviceRec["mytype"]:
        case "firewall" | "wrouter" | "server":
            return True
    return False


def powerOff(deviceRec):
    """return true if the device is powered off"""
    return not Device(deviceRec).powered_on


def isWirelessForwarder(deviceRec):
    """return true if the device is a wireless device that does forwarding, false if it does not"""
    if deviceRec is None:
        return False
    match deviceRec.get("mytype"):
        case "wrepeater" | "wap" | "wbridge" | "wrouter":
            return True
    return False


def linkConnectedToNic(nicRec):
    """Find a link connected to the specified network card"""
    if nicRec is None:
        return None
    logging.debug("looking for link connecting to nicid: "+ nicRec['myid']['nicid'])
    logging.debug("  Looking at nic: " + nicRec['nicname'])
    for one in session.puzzle.links:
        if one:
            # print ("   link - " + one['hostname'])
            if one["SrcNic"]["nicid"] == nicRec["myid"]["nicid"]:
                return one
            if one["DstNic"]["nicid"] == nicRec["myid"]["nicid"]:
                return one
    # we did not find anything that matched.  Return None
    return None


def getDeviceNicFromLinkNicRec(tLinkNicRec):
    """
    return the interface that the link connects to
    Args:
    tLinkNicRec:link-Nic-rec.  This should be link['SrcNic'] or link['DstNic']
    returns: the interface record or None
    """
    # a nic rec looks like: { "hostid": "100", "nicid": "102", "hostname": "pc0", "nicname": "eth0" }
    tNic = session.puzzle.nic_from_uid(tLinkNicRec["nicid"])
    if tNic is None:
        return None
    # If we get here, we have the nic record.
    return tNic


def routeRecFromDestIP(theDeviceRec, destinationIPString: str):
    """return a routing record given a destination IP string.  The device record has the route, nic, interface, and gateway"""
    # go through the device routes.
    if packet.isEmpty(destinationIPString):
        return None
    
    routeRec = {}
    if "route" not in theDeviceRec:
        theDeviceRec["route"] = []
    if not isinstance(theDeviceRec["route"], list):
        theDeviceRec["route"] = [theDeviceRec["route"]]  # turn it into a list
    for oneroute in theDeviceRec["route"]:
        tstring = oneroute["ip"] + "/" + oneroute["mask"]
        # logging.debug(f" the string is {tstring}")
        staticroute = ipaddress.ip_network(
            oneroute["ip"] + "/" + oneroute["mask"], strict=False
        )
        if destinationIPString in staticroute:
            # We found a gateway that we should use.
            routeRec["gateway"] = oneroute["gateway"]  # just the gateway
            break

    # if not a device route, look through nics
    if "gateway" not in routeRec:
        # We did not find it in the static routes.  Loop through all nics and see if one is local
        for oneNic in theDeviceRec["nic"]:
            localInterface = findLocalNICInterface(destinationIPString, oneNic)
            if localInterface is not None:
                # We found it.  Use it.
                routeRec["nic"] = oneNic
                routeRec["interface"] = localInterface
                break

    # if not a nic, use the default gateway
    if "gateway" not in routeRec and "nic" not in routeRec:
        # use the device default gateway
        routeRec["gateway"] = theDeviceRec["gateway"]["ip"]

    # if we have a gateway but do not know the nic and interface, find the right one
    if "gateway" in routeRec and "nic" not in routeRec:
        for oneNic in theDeviceRec["nic"]:
            localInterface = findLocalNICInterface(routeRec["gateway"], oneNic)
            if localInterface is not None:
                # We found it.  Use it.
                routeRec["nic"] = oneNic
                routeRec["interface"] = localInterface
                break

    # We should now have a good routeRec.  gateway might be blank, if it is local
    # But we should have a nic and interface set
    if "interface" not in routeRec:
        # We could not figure out the route.  return None.
        return None
    return routeRec


def canUseDHCP(srcDevice):
    for nic in Device(srcDevice).all_nics():
        if nic.get("usesdhcp") == "True":
            return True
    return False


def deviceFromIP(what):
    """Return the device, given a name
    Args: what:int the unique id of the device
    returns the device matching the id, or None"""
    for oneDevice in session.puzzle.devices:
        if oneDevice:
            for oneNic in oneDevice["nic"]:
                if not isinstance(oneNic["interface"], list):
                    oneNic["interface"] = [oneNic["interface"]]
                for oneInterface in oneNic["interface"]:
                    if oneInterface["myip"]["ip"] == what:
                        return oneDevice
    return None


def destIP(srcDevice, dstDevice):
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
    if srcDevice is None:
        logging.error("Error: function destIP: None passed in as source.")
        return None
    if dstDevice is None:
        logging.error("Error: function destIP: None passed in as destination.")
        return None
    if "hostname" not in srcDevice:
        logging.error("Error: function destIP: Not a valid source device.")
        return None
    if "hostname" not in dstDevice:
        logging.error("Error: function destIP: Not a valid destination device.")
        return None
    srcIPs = DeviceIPs(srcDevice)
    dstIPs = DeviceIPs(dstDevice)
    # logging.debug(f"we have IPs: src {len(srcIPs)} dst {len(dstIPs)}")
    # logging.debug(f"we have IPs: src {srcIPs} dst {dstIPs}")

    if srcIPs is None or dstIPs is None:
        # we will not be able to find a match.
        return None
    for oneSip in srcIPs:
        for oneDip in dstIPs:
            # compare each of them to find one that is local
            if oneSip in oneDip.network:
                # We found a match.  We are looking for the destination.  So we return that
                return oneDip
    # if we get here, we did not find a match
    for oneDip in dstIPs:
        # compare each of them to find one that is local
        if ipaddress.IPv4Interface(dstDevice.get("gateway")["ip"]) in oneDip.network:
            return oneDip
    # we need to find the IP address that is local to the gateway and use that.
    oneDip = ipaddress.IPv4Interface(srcDevice.get("gateway")["ip"])
    return oneDip


def sourceIP(src, dstIP):
    """
    Find the IP address to use when pinging the destination.  If the address is local, use the local nic.
    If the address is at a distance, we use the IP address associated with whatever route gets us there.
    Args:
        src:str - use the hostname as the source
        src:device - use src as the source device
        destIP:str - connect to this ip.  Eg: "192.168.1.1"
    return: an IP address string, or None
    """
    srcDevice = src
    if "hostname" not in src:
        srcDevice = session.puzzle.device_from_name(src)
    if srcDevice is None:
        logging.error("Error: passed in an invalid source to function: sourceIP")
        return None
    # Get all the IPs from this device
    allIPs = DeviceIPs(src)
    if allIPs is None:
        return None

    # return the IP that has a static route to it (add this later).
    if "route" in srcDevice:
        if not isinstance(srcDevice["route"], list):
            srcDevice["route"] = [srcDevice["route"]]
        for oneroute in srcDevice["route"]:
            staticroute = ipaddress.ip_network(
                oneroute["ip"] + "/" + oneroute["mask"], False
            )
            logging.info(f"We are looking for a static route to: {staticroute}")
            if dstIP in staticroute:
                # We found the route.  But we need to find the IP address that is local to the route
                routeip = ipaddress.ip_network(
                    oneroute["gateway"] + "/" + oneroute["mask"], False
                )
                logging.info("A static route matched.  Finding the IP for that route")
                # logging.info(f"looking for {routeip} through routes {allIPs}")
                for oneip in allIPs:
                    # oneip=ipaddress.IPv4Interface
                    if oneip in routeip:
                        logging.info(
                            "We found a local interface that worked with the route"
                        )
                        logging.debug(oneip.ip)
                        return oneip

    # return the IP that is local to the dest IP
    for oneip in allIPs:
        # oneip=ipaddress.IPv4Interface
        if dstIP in oneip.network:
            logging.info("We found a local network ")
            logging.debug(oneip.ip)
            return oneip
    # if we get here, we do not have a nic that is local to the destination.  Return the nic that the GW is on
    tmpval = f"{srcDevice['gateway']['ip']}/{srcDevice['gateway']['mask']}"
    GW = ipaddress.IPv4Interface(tmpval)
    for oneip in allIPs:
        if GW in oneip.network:
            # print("The gateway is the way forward ")
            # print(oneip.ip)
            return oneip

    # if we do not have a GW, we need to report, "no route to host"
    logging.info(
        f"sourceIP Giving 'No Route to host' from {srcDevice['hostname']} when looking for {dstIP}"
    )
    session.print("No route to host")
    return None


def deviceCaptions(deviceRec, howmuch: str):
    """
    return a list of strings, giving information about this device.
    Args:
        deviceRec - a device record.  pc0, laptop0, etc.
        howmuch:str - one of: 'none', 'full', 'host','host_ip','ip'
    returns an array of strings to be printed next to each device
    """
    captionstrings = []
    match howmuch:
        # case 'none':
        #
        case "full":
            captionstrings.append(deviceRec["hostname"])
            captionstrings.append(allIPStrings(deviceRec), True, True)
        case "host":
            captionstrings.append(deviceRec["hostname"])
        case "host_ip":
            captionstrings.append(deviceRec["hostname"])
            captionstrings.append(allIPStrings(deviceRec))
        case "ip":
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
    interfacelist = []
    srcDevice = src
    if "hostname" not in src:
        srcDevice = session.puzzle.device_from_name(src)
    if srcDevice is None:
        logging.error("Error: passed in an invalid source to function: sourceIP")
        return None
    if not isinstance(srcDevice["nic"], list):
        # If it is not a list, turn it into a list so we can iterate it
        srcDevice["nic"] = [srcDevice["nic"]]
    for onenic in srcDevice["nic"]:
        # Pull out all the nic interfaces
        if not isinstance(onenic["interface"], list):
            # turn it into a list so we can iterate it
            onenic["interface"] = [onenic["interface"]]
        for oneinterface in onenic["interface"]:
            # add it to the list
            if oneinterface["nicname"] == "lo0" and ignoreLoopback:
                # skip this interface if we are told to do so
                continue
            # print("Making list of ips:" + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            interfacelist.append(
                ipaddress.IPv4Interface(
                    oneinterface["myip"]["ip"] + "/" + oneinterface["myip"]["mask"]
                )
            )
    return interfacelist


def allIPStrings(src, ignoreLoopback=True, appendInterfacNames=False):
    """
    Return a list of all the ip addresses (IP+subnet) the device has.
    Args:
        src:str - the hostname of the device
        src:device - the device record itself
        ignoreLoopback:bool=True - whether to ignore the loopback
        appendInterfacNames:bool=False Add the interface names to the string - used for showing the status
    Returns:
        A list of strings (ip+mask)
    """
    interfacelist = []
    srcDevice = src
    if "hostname" not in src:
        srcDevice = session.puzzle.device_from_name(src)
    if srcDevice is None:
        logging.error("Error: passed in an invalid source to function: sourceIP")
        return None
    if not isinstance(srcDevice["nic"], list):
        # If it is not a list, turn it into a list so we can iterate it
        srcDevice["nic"] = [srcDevice["nic"]]
    for onenic in srcDevice["nic"]:
        # Pull out all the nic interfaces
        if not isinstance(onenic["interface"], list):
            # turn it into a list so we can iterate it
            onenic["interface"] = [onenic["interface"]]
        if onenic["nictype"][0] == "port" or onenic["nictype"][0] == "wport":
            # skip this interface if we are told to do so
            continue
        for oneinterface in onenic["interface"]:
            # add it to the list
            if oneinterface["nicname"] == "lo0" and ignoreLoopback:
                # skip this interface if we are told to do so
                continue
            # print("Making list of ips:" + oneinterface['myip']['ip'] + "/" + oneinterface['myip']['mask'])
            if appendInterfacNames:
                interfacelist.append(
                    oneinterface["nicname"]
                    + " "
                    + oneinterface["myip"]["ip"]
                    + "/"
                    + oneinterface["myip"]["mask"]
                )
            else:
                interfacelist.append(
                    oneinterface["myip"]["ip"] + "/" + oneinterface["myip"]["mask"]
                )
    return interfacelist


def interfaceIP(interfaceRec):
    """pull out the interface IP address for the specified interface.  Put it into a function so we can make it work for IPv4 and IPv6"""
    return interfaceRec["myip"]["ip"] + "/" + interfaceRec["myip"]["mask"]


def deviceHasIP(deviceRec, IPString: str):
    if deviceRec is None:
        return None
    tocheck = packet.justIP(IPString)
    for oneIP in allIPStrings(deviceRec):
        if tocheck == packet.justIP(oneIP):
            return True
    return False


def findLocalNICInterface(targetIPstring: str, networkCardRec):
    """Return the network interface record that has an IP address that is local to the IP specified as the target
    Args:
        targetIPstring:str - a string IP address, which we are trying to find a local interface for
        networCardRec:nicRecord - a netetwork card record, which may contain multiple interfaces
    returns: the interface record that is local to the target IP, or None"""
    if networkCardRec is None:
        return None
    if networkCardRec["nictype"][0] == "port":
        return None  # Ports have no IP address
    # loop through all the interfaces and return any that might be local.
    if not isinstance(networkCardRec["interface"], list):
        networkCardRec["interface"] = [
            networkCardRec["interface"]
        ]  # turn it into a list if needed.
    for oneIF in networkCardRec["interface"]:
        if packet.isLocal(targetIPstring, interfaceIP(oneIF)):
            return oneIF
    return None


def findPrimaryNICInterface(networkCardRec):
    """return the primary nic interface.  Turns out this is always interface 0"""
    if len(networkCardRec["nictype"]) > 0:
        return networkCardRec["nictype"][0]
    return None


def doInputFromLink(packRec, nicRec):
    # figure out what device belongs to the nic
    thisDevice = session.puzzle.device_from_uid(nicRec["myid"]["hostid"])

    # Do the simple stuff
    if powerOff(thisDevice):
        packRec["status"] = "done"
        # nothing more to be done
        return False

    if device_is_frozen(thisDevice):
        packRec["status"] = "done"
        # nothing more to be done
        return False
    # If the packet is a DHCP answer, process that here.  To be done later
    # If the packet is a DHCP request, and this is a DHCP server, process that.  To be done later.

    # Find the network interface.  It might be none if the IP does not match, or if it is a switch/hub device.
    tInterface = findLocalNICInterface(packRec["tdestIP"], nicRec)
    # if this is None, try the primary interface.
    if tInterface is None:
        tInterface = findPrimaryNICInterface(nicRec)
    # the interface still might be none if we are a switch/hub port
    # Verify the interface.  This is mainly to work with SSIDs, VLANs, VPNs, etc.
    if tInterface is not None:
        beginIngressOnInterface(packRec, tInterface)

    # the packet status should show dropped or something if we have a problem.
    # but for now, pass it onto the NIC
    return beginIngressOnNIC(packRec, nicRec)
    # The NIC passes it onto the device if needed.  We are done with this.


def beginIngressOnNIC(packRec, nicRec):
    """Begin the packet entering a device.  It enters via a nic, and then is processed.
    Args:
        packetRec: a packet record - the packet entering the device
        nicRec: a network card record - the nic on the device that we are entering.
    returns: nothing
    """
    # Notes from EduNetworkBuilder
    # Check to see if we have tests that break stuff.
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
    nictype = nicRec["nictype"][0]
    # in certain cases we track inbound traffic; remembering where it came from.
    trackPackets = False
    theDevice = session.puzzle.device_from_name(nicRec.get("myid").get("hostname"))
    # if it is a port (swicth/hub) or wport (wireless devices)
    if nictype == "port" or nictype == "wport":
        trackPackets = True
    if isWirelessForwarder(theDevice) and nictype == "wlan":
        trackPackets = True
    if nictype == "port" and theDevice["mytype"] == "wap":
        trackPackets = True
    if trackPackets:
        # We need to track ARP.  Saying, this MAC address is on this port. Simulates STP (Spanning Tree Protocol)
        if "port_arps" not in theDevice:
            theDevice["port_arps"] = {}
        if packRec.get("sourceMAC") not in theDevice.get("port_arps"):
            theDevice["port_arps"][packRec.get("sourceMAC")] = nicRec.get("nicname")

    # Look better tracking for network loops
    # If the same packet hits the same switch, we determine it is a loop
    hostname = theDevice.get("hostname")
    if "path" not in packRec:
        packRec["path"] = []
    # Check if the hostname is already in the path of the packet.  If so, it is a loop
    if hostname in packRec.get("path"):
        session.packetstorm = True
    packRec["path"].append(hostname)

    # If we are entering a WAN port, see if we should be blocked or if it is a return packet
    if nictype == "wan":
        pass
        # We do not have the firewall programed in yet.
        # if the packet is a return ping packet, allow it. Otherwise, reject

    if (
        packRec["destMAC"] == nicRec["Mac"]
        or packet.isBroadcastMAC(packRec["destMAC"])
        or nictype == "port"
        or nictype == "wport"
    ):
        # The packet is good, and has reached the computer.  Pass it on to the device
        # print ("Packet entering device: " + theDevice['hostname'])
        return packetEntersDevice(packRec, theDevice, nicRec)
    else:
        # print("packet did not match.  Dropping")
        # print (packRec)
        # print("  packet dst MAC" + packRec['destMAC'] + " vs this NIC" + nicRec['Mac'])
        packRec["status"] = "dropped"
        return False


def beginIngressOnInterface(packRec, interfaceRec):
    """Here we would do anything needed to be done with the interface.
    VLAN
    SSID
    Tunnel/VPN
    """
    # right now, we let pass it back
    return True


def packetEntersDevice(packRec, thisDevice, nicRec):
    """When a packet enters a device, coming from an interface and network card.  Here we respond to stuff, route, or switch..."""
    if powerOff(thisDevice):
        packRec["status"] = "done"
        # nothing more to be done
        return False
    # We would check if it was frozen.  That is a test, not a status.  We do not have that check yet.

    # Deal with DHCP.
    # If it is a request and this is a DHCP server, serve an IP back.
    if packRec["packettype"] == "DHCP-Request":
        if servesDHCP(thisDevice):
            if (
                "isdhcp" in thisDevice
                and thisDevice["isdhcp"] == "True"
                and "dhcprange" in thisDevice
            ):
                session.print(f"Arrived at DHCP server: {thisDevice['hostname']}")
                makeDHCPResponse(packRec, thisDevice, nicRec)
                packRec["status"] = "done"
                return True
    # If it is a DHCP answer, update the device IP address.
    if packRec["packettype"] == "DHCP-Response":
        if packRec["destMAC"] == nicRec["Mac"] and nicRec.get("usesdhcp") == "True":
            logging.info(
                f"Recieved DHCP response.  Dealing with it. payload: {packRec['payload']}"
            )
            logging.info("packet matches this nic.")
            session.ui.parser.parse(
                f"set {thisDevice['hostname']} {nicRec['nicname']} {packRec['payload']['ip']}/{packRec['payload']['subnet']}",
                False,
            )
            if packet.isEmpty(thisDevice["gateway"]["ip"]):
                session.ui.parser.parse(
                    f"set {thisDevice['hostname']} gateway {packRec['payload']['gateway']}"
                )
            packRec["status"] = "done"
            return True

    # If the packet is destined for here, process that
    # print("Checking destination.  Looking for " + packet.justIP(packRec['destIP']))
    # print("   Checking against" + str(allIPStrings(thisDevice)))
    if routesPackets(thisDevice) or deviceHasIP(thisDevice, packRec["destIP"]):
        packRec["TTL"] = (
            packRec.get("TTL", 0) - 1
        )  # decrement the ttl with every router
        if packRec["TTL"] <= 0:
            if packRec["packettype"] == "traceroute-request":
                # We need to bounce a response back
                dest = deviceFromIP(packet.justIP(str(packRec["sourceIP"])))
                logging.info(
                    f"A traceroute timed out at {thisDevice['hostname']}.  Making a return packet"
                )
                # we need to generate a traceroute response
                nPacket = packetFromTo(thisDevice, dest)
                nPacket["packettype"] = "traceroute-response"
                nPacket["payload"] = packRec["payload"]
                sendPacketOutDevice(nPacket, thisDevice)
                nPacket["payload"]["tempDest"] = nPacket["sourceIP"]
                # print (nPacket)
                packet.addPacketToPacketlist(nPacket)
                packRec["status"] = "done"
                return True

    if deviceHasIP(thisDevice, packRec["destIP"]):
        packRec["status"] = "done"
        logging.info("Packet arrived at destination")
        #        print ("packet type: -" + packRec['packettype'] + "-")

        # ping, send ping packet back
        if packRec["packettype"] == "ping":
            # logging.debug(f"Returning packet: {packRec}")
            # logging.debug(f"Returning packet: {packRec['sourceIP']} - {packet.justIP(str(packRec["sourceIP"]))}")
            dest = deviceFromIP(packet.justIP(str(packRec["sourceIP"])))
            # logging.info(f"A ping came.  Making a return packet going to {dest}")
            # print (packet.justIP(str(packRec['sourceIP'])))
            # print(dest)
            # we need to generate a ping response
            nPacket = packetFromTo(thisDevice, dest)
            nPacket["packettype"] = "ping-response"
            sendPacketOutDevice(nPacket, thisDevice)
            # print (nPacket)
            packet.addPacketToPacketlist(nPacket)
            packRec["status"] = "done"
            return True

        # ping response, mark it as done
        if packRec["packettype"] == "ping-response":
            logging.info("Woot! We returned with a ping")
            packRec["status"] = "done"
            pingsrcip = packet.justIP(packRec.get("destIP"))
            srcip = pingdestip = packet.justIP(packRec.get("sourceIP"))
            pingdest = deviceFromIP(pingdestip)
            logging.info(f"sourceip is {srcip}")
            logging.info(f"dest host is {pingdest.get('hostname')}")
            if packRec["health"] < 100:
                logging.info(
                    f"Packet was damaged during transit.  Not complete success: Health={packRec['health']}"
                )
                session.print(
                    f"PING: {pingsrcip} -> {pingdestip}: Partial Success! - Packet damaged in transit.  Health={packRec['health']}"
                )
            else:
                session.print(f"PING: {pingsrcip} -> {pingdestip}: Success!")
            if pingdest is not None and packRec["health"] == 100:
                mark_test_as_completed(
                    thisDevice.get("hostname"),
                    pingdest.get("hostname"),
                    "SuccessfullyPings",
                    f"Successfully pinged from {thisDevice.get('hostname')} to {pingdest.get('hostname')}",
                )
                # We mark this as complete too, but the test for 'WithoutLoop' happens later
                mark_test_as_completed(
                    thisDevice.get("hostname"),
                    pingdest.get("hostname"),
                    "SuccessfullyPingsWithoutLoop",
                    f"Successfully pinged from {thisDevice.get('hostname')} to {pingdest.get('hostname')} without a network loop.",
                )

                # print(f" we are done, and packetlist is: {len(session.packetlist)} and storm: {session.packetstorm}")
            return True

        if packRec["packettype"] == "traceroute-response":
            # We need to determine what machine responded.  If it was the true dest, we are done.
            # If not, we need to send out a packet with a longer TTL
            packRec["status"] = "done"
            if packRec["payload"]["tempDest"] is None:
                return False
            print(
                f" We are looking at a packet from {packRec['payload']['tempDest']} and the final destination should be {packRec['payload']['origDestIP']}"
            )
            if packRec["payload"]["tempDest"] != packRec["payload"]["origDestIP"]:
                # It is not the right dest.  Try again
                sdev = session.puzzle.device_from_name(
                    packRec["payload"]["origSHostname"]
                )
                ddev = session.puzzle.device_from_name(
                    packRec["payload"]["origDHostname"]
                )
                print(
                    f"Making new traceroute from {sdev['hostname']} to {ddev['hostname']} with TTL {packRec['payload']['origTTL'] + 1}"
                )
                if packRec["payload"]["origTTL"] + 1 < 10:
                    Traceroute(sdev, ddev, packRec["payload"]["origTTL"] + 1)
            else:
                pingsrcip = packet.justIP(packRec.get("destIP"))
                srcip = pingdestip = packet.justIP(packRec.get("sourceIP"))
                pingdest = deviceFromIP(pingdestip)
                if packRec["health"] < 100:
                    logging.info(
                        f"Packet was damaged during transit.  Not complete success: Health={packRec['health']}"
                    )
                    session.print(
                        f"PING: {pingsrcip} -> {pingdestip}: Partial Success! - Packet damaged in transit.  Health={packRec['health']}"
                    )
                else:
                    session.print(f"Traceroute: {pingsrcip} -> {pingdestip}: Success!")
                if pingdest is not None and packRec["health"] == 100:
                    mark_test_as_completed(
                        thisDevice.get("hostname"),
                        pingdest.get("hostname"),
                        "SuccessfullyTraceroutes",
                        f"Successfully ran traceroute from {thisDevice.get('hostname')} to {pingdest.get('hostname')}",
                    )
            return True

    # If the packet is not done and we forward, forward. Basically, a switch/hub
    if packRec["status"] != "done" and forwardsPackets(thisDevice):
        send_out_hubswitch(thisDevice, packRec, nicRec)
        return
    # if the packet is not done and we route, route
    if packRec["status"] != "done" and routesPackets(thisDevice):
        # print("routing")
        sendPacketOutDevice(packRec, thisDevice)
        return
    # If we get here, we might have forwarded.  If so, we mark the old packet as done.
    packRec["status"] = "done"


def send_out_hubswitch(thisDevice, packRec, nicRec = None):
    # We loop through all nics. (minus the one we came in from)
        onlyport = ""
        if thisDevice.get("mytype") == "net_switch":
            if packRec.get("destMAC") in thisDevice.get("port_arps", {}):
                # we just send this out the one port.
                onlyport = thisDevice.get("port_arps").get(packRec.get("destMAC"))
        # print("We are forwarding.")
        for onenic in thisDevice["nic"]:
            # we duplicate the packet and send it out each port-type
            # find the link connected to the port
            # print ("Should we send out port: " + onenic['nicname'])
            tlink = linkConnectedToNic(onenic)
            if (
                tlink is not None
                and 
                ( nicRec is None
                 or
                 nicRec["uniqueidentifier"] != onenic["uniqueidentifier"]
                )
            ):
                # We have a network wire connected to the NIC.  Send the packet out
                # if it is a switch-port, then we check first if we know where the packet goes - undone
                if onlyport == "" or onlyport == onenic.get("nicname"):
                    tpacket = copy.deepcopy(packRec)
                    tpacket["packetlocation"] = tlink["hostname"]
                    tpacket["packetDistance"] = (
                        0  # reset it to the beginning of the next link
                    )
                    if tlink["SrcNic"]["hostname"] == thisDevice["hostname"]:
                        tpacket["packetDirection"] = 1  # Src to Dest
                    else:
                        tpacket["packetDirection"] = 2  # Dest to Source
                    tpacket["packetDistance"] = 0  # start at the beginning.
                    packet.addPacketToPacketlist(tpacket)
                    # print (" Sending packet out a port: " + tpacket['packetlocation'])
        # we set this packet as done.
        packRec["status"] = (
            "done"  # The packet that came in gets killed since it was replicated everywhere else
        )

def makeDHCPResponse(packRec, thisDevice, nicRec):
    if "dhcplist" not in thisDevice:
        thisDevice["dhcplist"] = {}
    inboundip = nicRec["interface"][0]["myip"]["ip"]
    iprange = None
    available_ip = ""  # start with it empty.  Fill it if we can
    for onerange in thisDevice["dhcprange"]:
        if onerange["ip"] == inboundip:
            iprange = onerange

    if iprange is not None:
        rangestart = int(
            iprange["mask"].split(".")[3]
        )  # they were stored a bit oddly in the original json
        rangeend = int(
            iprange["gateway"].split(".")[3]
        )  # they were stored a bit oddly in the original json
        iparr = iprange["ip"].split(".")
        ipprepend = f"{iparr[0]}.{iparr[1]}.{iparr[2]}."
        for i in range(rangestart, rangeend):
            newip = ipprepend + str(i)
            found = False
            for dhcpentry in thisDevice["dhcplist"].values():
                if dhcpentry == newip:
                    found = True
                    break
            if not found:
                available_ip = newip
                break
    # Now, check to see if we have an entry already.
    if packRec["sourceMAC"] in thisDevice["dhcplist"]:
        # we already have an entry. Use it
        available_ip = thisDevice["dhcplist"][packRec["sourceMAC"]]
    else:
        logging.debug(
            f"DHCP: Making an IP reservation {available_ip} {packRec['sourceMAC']}"
        )

    if available_ip != "":
        # stash it.  if it already exists, we use the same value.
        thisDevice["dhcplist"][packRec["sourceMAC"]] = available_ip
        # Now, make a new DHCP response packet
        nPacket = packet.newPacket()
        nPacket["sourceIP"] = nicRec["interface"][0]["myip"]["ip"]
        nPacket["sourceMAC"] = nicRec.get("Mac")
        nPacket["destIP"] = "0.0.0.0"
        nPacket["destMAC"] = packRec["sourceMAC"]
        nPacket["packettype"] = "DHCP-Response"
        nPacket["payload"] = {
            "ip": available_ip,
            "subnet": nicRec["interface"][0]["myip"]["mask"],
            "gateway": thisDevice["gateway"]["ip"],
        }
        destlink = linkConnectedToNic(nicRec)
        nPacket["packetlocation"] = destlink["hostname"]
        if destlink["SrcNic"]["hostname"] == thisDevice["hostname"]:
            nPacket["packetDirection"] = 1  # Src to Dest
        else:
            nPacket["packetDirection"] = 2  # Dest to Source
        packet.addPacketToPacketlist(nPacket)
        logging.info(
            f"Responding to dhcp request.  Assigned IP: {available_ip} to mac {packRec['sourceMAC']}"
        )


# def AssignMacIfNeeded(nicRec):
#     if 'Mac' not in nicRec:
#         #Most of the network cards do not have this done yet.  We generate a new random one
#         localmac=""
#         for i in range(1,13):
#             localmac=localmac+random.choice("ABCDEF1234567890")
#         nicRec['Mac']=localmac


def sendPacketOutDevice(packRec, theDevice):
    """Send the packet out of the device."""
    # print("Sending packet out a device: " + theDevice['hostname'])
    # determine which interface/nic we are exiting out of - routing
    packRec["packetDistance"] = 0  # always reset this
    routeRec = routeRecFromDestIP(theDevice, packRec["destIP"])
    destlink = None
    # set the source MAC address on the packet as from the nic
    if routeRec is not None:
        logging.debug("Found a route rec.")
        routeRec["nic"] = Nic(routeRec["nic"]).ensure_mac()
        packRec["sourceMAC"] = routeRec["nic"]["Mac"]
        # set the destination MAC to be the GW MAC if the destination is not local
        # this needs an ARP lookup.  That currently is in puzzle, which would make a circular include.
        if (
            packRec["destMAC"] != packet.BroadcastMAC()
            and packRec["packettype"] != "DHCP-Response"
        ):
            if routeRec.get("gateway") is not None:
                # We are going out the gateway.  Find the ARP for that
                packRec["destMAC"] = globalArpLookup(routeRec.get("gateway"))
            else:
                # We are on a local link.  Set the destmac to be the mac of our destination computer
                packRec["destMAC"] = globalArpLookup(packRec.get("destIP"))

        if routeRec["nic"]["nicname"] == "management_interface0":
            #If we are exiting a switch / hub; we go out the ports
            send_out_hubswitch(theDevice, packRec)
            return
        else:
            # set the packet location being the link associated with the nic
            #   Fail if there is no link on the port
            destlink = linkConnectedToNic(routeRec["nic"])

    if destlink is not None:
        packRec["packetlocation"] = destlink["hostname"]
        if destlink["SrcNic"]["hostname"] == theDevice["hostname"]:
            packRec["packetDirection"] = 1  # Src to Dest
        else:
            packRec["packetDirection"] = 2  # Dest to Source
        return True
    # If we get here, it did not work.  No route to host.
    # right now, we blow up.  We need to deal with this with a bit more grace.  Passing the error back to the user
    packRec["status"] = "failed"
    logging.info(
        f"sendpacketoutdevice Giving 'No Route to host' from {theDevice['hostname']} when looking for {packRec['destIP']}"
    )
    session.print("No route to host")


def ensureHostRec(item):
    """Return a device from either a hostname or a device
    Args: item: string or device
    returns: a device structure"""
    newitem = item
    if "hostname" not in item:
        # The function is being improperly used. Can we fix it?
        newitem = session.puzzle.device_from_name(item)
        if newitem is None:
            # we were unable to fix it.  Complain bitterly
            logging.error(
                "Error: invalid source passed to ensureHostRec.  item must be a device."
            )
            return None
    return Device(newitem)


def ensureHostname(item):
    """Return a hostname from either a hostname or a device
    Args: item: string or device
    returns: a valid hostname"""
    hostname = item
    if "hostname" in item:
        hostname = item["hostname"]
    # The function is being improperly used. Can we fix it?
    newitem = session.puzzle.device_from_name(item)
    if newitem is None:
        # somehow it was an invalid hostname
        logging.error("Error: invalid hostname passed to ensureHostname.")
        return None
    return hostname


def packetFromTo(src, dest):
    """Generate a packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
    """
    # src should be a device, not just a name.  Sanity check.
    # logging.debug(f"starting a packet from {src} to {dest}")
    if "hostname" not in src:
        # The function is being improperly used. Can we fix it?
        newsrc = session.puzzle.device_from_name(src)
        if newsrc is not None:
            src = newsrc
        else:
            # we were unable to fix it.  Complain bitterly
            logging.error(
                "Error: invalid source passed to packetFromTo.  src must be a device."
            )
            return None
    if src is None:
        # the function is being improperly used
        logging.error(
            "Error: packetFromTo function must have a valid device as src.  None was passed in."
        )
        return None
    # dest should be a device, an ip address, or a hostname
    if dest is None:
        logging.error(
            "Error: You must have a destination for packetFromTo.  None was passed in."
        )
        return None
    if isinstance(dest, str) and not packet.is_ipv4(dest):
        # If it is a string, but not a string that is an IP address
        # print("using dest as a hostname")
        dest = session.puzzle.device_from_name(dest)
    if "hostname" in dest:
        # print ("getting destination IP from a device")
        # If we passed in a device or hostname, convert it to an IP
        logging.debug(f"Finding the IP for dest {dest['hostname']} ")
        dest = destIP(src, dest)
        if dest is not None:
            logging.debug(f"Found IP {dest}")

    if dest is None or packet.isEmpty(dest):
        # This means we were unable to figure out the dest.  No such host, or something
        logging.info(f"Error: Not a valid target: {dest}")
        session.print(f"Not a valid target {dest}")
        return None
    if isinstance(dest, ipaddress.IPv4Address):
        # This is what we are hoping for.
        nPacket = packet.newPacket()  # make an empty packet
        nPacket["sourceIP"] = sourceIP(src, dest)
        # packet['sourceMAC'] = #the MAC address of the above IP
        nPacket["sourceMAC"] = arpLookup(src, nPacket["sourceIP"])
        # packet['destIP'] = #figure this out
        nPacket["destIP"] = dest  # this should now be the IP
        # packet['destMAC'] = #If the IP is local, we use the MAC of the host.  Otherwise it is the MAC of the gateway
        nPacket["destMAC"] = globalArpLookup(dest)
        nPacket["packettype"] = ""
        return nPacket


def Ping(src, dest):
    """Generate a ping packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
    """
    nPacket = packetFromTo(src, dest)
    if nPacket is not None:
        nPacket["packettype"] = "ping"
        sendPacketOutDevice(nPacket, src)
        # print (nPacket)
        packet.addPacketToPacketlist(nPacket)


def Traceroute(src, dest, newTTL=1):
    """Generate a traceroute packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
    """
    srchost = ensureHostRec(src)
    desthost = ensureHostRec(dest)
    nPacket = packetFromTo(src, dest)
    nPacket["packettype"] = "traceroute-request"
    nPacket["TTL"] = newTTL  # This is the secret to the traceroute.
    nPacket["payload"] = {
        "origTTL": newTTL,  # We will increase this as we go out.
        "origSHostname": srchost.hostname,
        "origSourceIP": nPacket["sourceIP"],
        "origDHostname": desthost.hostname,
        "origDestIP": nPacket["destIP"],
    }
    logging.info(
        f"Starting traceroute packet from {srchost.hostname} to {desthost.hostname}"
    )
    sendPacketOutDevice(nPacket, src)
    # print (nPacket)
    packet.addPacketToPacketlist(nPacket)


def doDHCP(srcHostname):
    """Generate a DHCP request packet from the specified hostname, if that host has any
    network cards that request DHCP
    Args:
        srcHostname:str the hostname to do a DHCP request on"""
    # see if we can do a dhcp request from the specified hostname
    srcDevice = session.puzzle.device_from_name(srcHostname)
    if srcDevice is None:
        session.print(f"No such host: {srcHostname}")
        return
    if not canUseDHCP(srcHostname):
        return
    for nic in Device(srcDevice).all_nics():
        if nic.get("usesdhcp") == "True":
            # This NIC can do DHCP.  Send out a request
            nPacket = packet.newPacket()
            # We do not know our IP, so we have no mask to determine.  Broadcast is done using the MAC
            nPacket["sourceIP"] = "0.0.0.0"
            # packet['sourceMAC'] = #the MAC address of the above IP
            nPacket["sourceMAC"] = nic.get("Mac")
            nPacket["destIP"] = "0.0.0.0"
            # packet['destMAC'] = #If the IP is local, we use the MAC of the host.  Otherwise it is the MAC of the gateway
            nPacket["destMAC"] = packet.BroadcastMAC()
            nPacket["packettype"] = "DHCP-Request"
            sendPacketOutDevice(nPacket, srcDevice)
            # print (nPacket)
            packet.addPacketToPacketlist(nPacket)


##############
# Net Tests
# def all_tests
# def device_is_locked
# def mark_as_completed
# The tests are:
# NetTestType { NeedsLocalIPTo, NeedsDefaultGW, NeedsLinkToDevice, NeedsRouteToNet,
#        NeedsUntaggedVLAN, NeedsTaggedVLAN, NeedsForbiddenVLAN,
#        SuccessfullyPings, SuccessfullyPingsAgain, SuccessfullyArps, SuccessfullyDHCPs, HelpRequest, ReadContextHelp, FailedPing,
#        DHCPServerEnabled, SuccessfullyTraceroutes, SuccessfullyPingsWithoutLoop,
#        LockAll, LockIP, LockRoute, LockNic, LockDHCP, LockGateway, LockLocation,
#        LockVLANsOnHost, LockNicVLAN, LockInterfaceVLAN, LockVLANNames,
#        DeviceIsFrozen, DeviceBlowsUpWithPower, DeviceNeedsUPS, DeviceNICSprays,
#    }
# nettest structure: shost, dhost, thetest


def all_tests(JustForHost=None):
    """This is a convenience function."""
    return session.puzzle.all_tests(JustForHost)


def device_is_critical(devicename):
    """This is a convenience function."""
    return session.puzzle.device_is_critical(devicename)


def device_is_frozen(devicename):
    """This is a convenience function."""
    return session.puzzle.device_is_frozen(devicename)


def item_is_locked(shost, whattocheck, dhost=None):
    """This is a convenience function."""
    return session.puzzle.item_is_locked(shost, whattocheck, dhost=None)


def has_test_been_completed(shost, dhost, whattocheck):
    """This is a convenience function."""
    return session.puzzle.has_test_been_completed(shost, dhost, whattocheck)


def mark_test_as_completed(shost, dhost, whattocheck, message):
    """This is a convenience function."""
    return session.puzzle.mark_test_as_completed(shost, dhost, whattocheck, message)


def commands_from_tests(JustForHost=None):
    """This is a convenience function."""
    return session.puzzle.commands_from_tests(JustForHost)
