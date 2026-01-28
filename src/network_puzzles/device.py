import ipaddress
import logging
from copy import deepcopy

from . import packet, session
from .core import ItemBase
from .nic import Nic
from .interface import Interface


class Device(ItemBase):
    def __init__(self, value=None, json_data=None):
        super().__init__(json_data)
        # Allow override of json data with passed "value" identifier.
        if value is not None:
            try:
                value = int(value)
            except (TypeError, ValueError):
                pass
            if isinstance(value, int):
                # Find device by uid; might return None
                json_data = session.puzzle.device_from_uid(value)
            # define the varables as specific types so intellisense works nicely with it
            elif isinstance(value, str):
                # Find device by hostname; might return None.
                json_data = session.puzzle.device_from_name(value)
            elif isinstance(value, dict):
                json_data = value
            else:
                raise ValueError(
                    f"Not a valid uniqueidentifier, hostname, or JSON data: {value}"
                )
            self.json = json_data if json_data else {}

    @property
    def frozen(self):
        return session.puzzle.device_is_frozen(self.json)

    @property
    def gateway(self) -> str:
        return self.json.get("gateway").get("ip", "")

    @gateway.setter
    def gateway(self, ip):
        if not self.json.get("gateway"):
            self.json["gateway"] = {
                "ip": "0.0.0.0",
                "mask": "0.0.0.0",
                "gateway": "0.0.0.0",
                "type": "gw",
            }
        self.json["gateway"]["ip"] = ip

    @property
    def hostname(self) -> str:
        return self.json.get("hostname", "")

    @hostname.setter
    def hostname(self, name):
        self.json["hostname"] = name

    @property
    def is_dhcp(self) -> bool:
        if self.json.get("isdhcp", "").lower() in ("true", "yes"):
            value = True
        else:
            value = False
        # logging.debug(f"{self.hostname}.is_dhcp {value=}")
        return value

    @is_dhcp.setter
    def is_dhcp(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["isdhcp"] = value

    @property
    def is_invisible(self) -> bool:
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
    def location(self) -> tuple:
        loc = self.json.get("location")
        if loc:
            location = loc.split(",")
            location = (int(location[0]), int(location[1]))
            return location
        raise ValueError(f"Invalid JSON location data for '{self.hostname}'")

    @property
    def mytype(self) -> str:
        return self.json.get("mytype", "")

    @property
    def powered_on(self) -> bool:
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
    def blown_up(self) -> bool:
        value = False
        if "blownup" in self.json:
            if self.json.get("blownup", "").lower() in ("true", "yes"):
                value = True
            else:
                value = False
            # logging.debug(f"{self.hostname}.powered_on: {value}")
        return value

    @blown_up.setter
    def blown_up(self, value):
        # we can only set it to true.  We cannot unset this value.
        # to make it 'false', we need to replace the device
        if (isinstance(value, bool) and value) or (
            isinstance(value, str) and value.lower() == "true"
        ):
            if isinstance(value, bool):
                value = str(value)
            self.json["blownup"] = value
            self.powered_on = True  # when it blows up, the power gets turned off

    @property
    def is_wireless_forwarder(self):
        """return true if the device is a wireless device that does forwarding, false if it does not"""
        if self.json is None:
            return False
        match self.mytype:
            case "wrepeater" | "wap" | "wbridge" | "wrouter":
                return True
        return False

    @property
    def serves_dhcp(self):
        """return true if the device can serve dhcp, false if it can not"""
        match self.mytype:
            case "firewall" | "wrouter" | "server":
                return True
        return False

    @property
    def size(self):
        return int(self.json.get("size"))

    @property
    def uniqueidentifier(self) -> str:
        return self.json.get("uniqueidentifier", "")

    def all_nics(self) -> list:
        if not isinstance(self.json.get("nic"), list):
            self.json["nic"] = [self.json["nic"]]
        return self.json.get("nic")

    def disable_nic_dhcp(self):
        for onenic in self.all_nics():
            # these come in json format.  Convert to a nic and define it
            Nic(onenic).uses_dhcp = False

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
                    try:
                        onemac = {
                            "ip": ipaddress.ip_interface(
                                oneinterface["myip"]["ip"]
                                + "/"
                                + oneinterface["myip"]["mask"]
                            ),
                            "mac": onenic["Mac"],
                        }
                        maclist.append(onemac)
                    except ValueError:
                        # If the IP is invalid, do not add it
                        continue
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

    # firewall pieces
    @property
    def CanDoFirewall(self):
        # If it does not exist at all
        if self.mytype == "firewall":
            return True
        if self.mytype == "wrouter":
            return True
        return False

    @property
    def HasAdvancedFirewall(self):
        # If it does not exist at all
        if "firewallrule" not in self.json:
            return False
        if len(self.json.get("firewallrule")) == 0:
            return False
        return True

    def AllFirewallRules(self):
        if not self.HasAdvancedFirewall:
            # it is an empty list
            return []
        if not isinstance(self.json.get("firewallrule"), list):
            # make sure it is a list.
            self.json["firewallrule"] = [self.json.get("firewallrule")]
        return self.json["firewallrule"]

    def AdvFirewallAllows(self, InInterface: str, OutInterface: str):
        if not self.HasAdvancedFirewall:
            return True  # We can go out the firewall if no rules
        # logging.debug("Testing firewall rule. in {InInterface} - out {OutInterface}")
        for onerule in self.AllFirewallRules():
            if (
                onerule.get("source") == InInterface
                and onerule.get("destination") == OutInterface
            ):
                # logging.debug("Found match.")
                if onerule.get("action") == "Drop" or onerule.get("action") == "drop":
                    return False
                if onerule.get("action") == "Allow" or onerule.get("action") == "allow":
                    return True
        # If no rules prohibit it, allow it.  Default policy
        return True

    def AdvFirewallAdd(self, InInterface: str, OutInterface: str, dropallow: str):
        logging.debug(
            "Adding firewall rule. in {InInterface} - out {OutInterface} - {dropallow}"
        )
        # if we have a rule with the same src/dest, we replace the target
        # if not, we add a new rule with the specified info
        for onerule in self.AllFirewallRules():
            if (
                onerule.get("source") == InInterface
                and onerule.get("destination") == OutInterface
            ):
                onerule["action"] = dropallow.lower()
                return True
        # If we get here, nothing yet matched.  Add a new record
        newfw = {
            "source": InInterface,
            "destination": OutInterface,
            "action": dropallow,
        }
        self.json["firewallrule"].append(newfw)
        return True

    def AdvFirewallDel(self, InInterface: str, OutInterface: str, dropallow: str):
        logging.debug(
            "Deleting firewall rule. in {InInterface} - out {OutInterface} - {dropallow}"
        )
        # if we have a rule with the same src/dest/targer, we drop it
        # if not, we return "false"
        for onerule in self.AllFirewallRules():
            if (
                onerule.get("source") == InInterface
                and onerule.get("destination") == OutInterface
                and onerule.get("action").lower() == dropallow.lower()
            ):
                self.json["firewallrule"].remove(onerule)
                return True
        # If we get here, nothing yet matched.  Add a new record
        return False

    # NAT-table functions
    # for tracking outbound packets on WAN network cards.
    def AddIPConnectionEntry(self, dest_ip, src_ip, packettype, response):
        """Add a record of the packet and what we should do when we encounter its response
        dest_ip: the IP address of the destination
        src_ip: the IP address of the source
        packettype: 'ping, ping-response, etc.
        response: One of  none|accept|masq|drop|reject"""
        if "IPConnections" not in self.json:
            self.json["IPConnections"] = []  # make an empty array

        newrec = {
            "dest": packet.justIP(dest_ip),
            "src": packet.justIP(src_ip),
            "packettype": packettype.lower(),
            "response": response.lower(),
            "masqsrc": packet.justIP(src_ip),
        }
        self.json["IPConnections"].append(newrec)
        return newrec

    def ReturnIPConnectionEntry(self, dest_ip, src_ip, packettype):
        """Look up and return the IP packet matching info, if it exists
        dest_ip: the IP address of the destination
        src_ip: the IP address of the source
        packettype: 'ping, ping-response, etc.
        response: One of  none|accept|masq|drop|reject"""

        check_type = packettype
        if packettype == "ping-response":
            check_type = 'ping'
        if packettype == "traceroute-request":
            check_type = 'traceroute-response'

        if "IPConnections" not in self.json:
            self.json["IPConnections"] = []  # make an empty array
            return None
        for onerec in self.json["IPConnections"]:
            logging.debug(f"checking for response {packet.justIP(dest_ip)}, {packet.justIP(src_ip)} {packettype} check_type: {check_type}")
            logging.debug(f"checking for response {onerec['dest']}, {onerec['src']} {onerec['packettype']}")
            if onerec['dest'] == packet.justIP(dest_ip) and onerec['src'] == packet.justIP(src_ip) and onerec['packettype'] == packettype:
                #outbound packet
                pass
        if onerec['src'] == packet.justIP(dest_ip) and onerec['dest'] == packet.justIP(src_ip) and onerec['packettype'] == check_type:
            logging.debug("found one!")
            return onerec
                
        return None

    def ClearIPConnections(self):
        self.json["IPConnections"] = [] #empty them

    def begin_ingress_on_nic(self, nic, pkt):
        """Begin the packet entering a device.  It enters via a nic, and then is processed.
        Args:
            nic: a `nic.Nic` object - the NIC the packet enters into
            pkt: a `packet.Packet` object - the packet entering the device
        returns: nothing
        """
        # logging.debug(f"Test: Device.begin_ingress_on_nic: {self.hostname}:{nic.name}")
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

        # in certain cases we track inbound traffic; remembering where it came from.
        trackPackets = False

        # if it is a port (swicth/hub) or wport (wireless devices)
        if nic.type[0] == "port" or nic.type[0] == "wport":
            trackPackets = True
        if self.is_wireless_forwarder and nic.type[0] == "wlan":
            trackPackets = True
        if nic.type[0] == "port" and self.mytype == "wap":
            trackPackets = True
        if trackPackets:
            # We need to track ARP.  Saying, this MAC address is on this port. Simulates STP (Spanning Tree Protocol)
            if "port_arps" not in self.json:
                self.json["port_arps"] = {}
            if pkt.source_mac not in self.json.get("port_arps"):
                self.json["port_arps"][pkt.source_mac] = nic.name

        # Look better tracking for network loops
        # If the same packet hits the same switch, we determine it is a loop
        # Check if the hostname is already in the path of the packet.  If so, it is a loop
        if self.hostname in pkt.path:
            session.packetstorm = True
        pkt.path.append(self.hostname)

        # If we are entering a WAN port, see if we should be blocked or if it is a return packet
        if nic.type[0] == "wan":
            connection_info = self.ReturnIPConnectionEntry(pkt.destination_ip, pkt.source_ip, pkt.packettype)
            if connection_info is not None:
                logging.debug(f"Found a return packet {connection_info}")
                if connection_info['response'] == 'masq':
                    logging.debug(f"Packet was masqueraded.  Switching it back {connection_info['src']} -> {connection_info['masqsrc']}")
                    pkt.destination_ip = connection_info['masqsrc']
            else:
                #we do not have a record of this.  Packets coming into the WAN, unless it is destined for here, are dropped.
                logging.debug("no record of this.  Drop it for now")
                pkt.status = "done"
                return False

        if (
            pkt.destination_mac == nic.mac
            or packet.is_broadcast_mac(pkt.destination_mac)
            or nic.type[0] == "port"
            or nic.type[0] == "wport"
        ):
            # The packet is good, and has reached the computer.  Pass it on to the device
            # print ("Packet entering device: {self.hostname}")
            return self.receive_packet(pkt, nic)
        else:
            # print("packet did not match.  Dropping")
            # print (pkt.json)
            # print("  packet dst MAC" + pkt.destination_mac + " vs this NIC" + nic.mac)
            pkt.status = "dropped"
            return False

    def receive_packet(self, pkt, nic):
        """When a packet enters a device, coming from an interface and network card.  Here we respond to stuff, route, or switch..."""
        # Ensure Packet object.
        if not isinstance(pkt, packet.Packet):
            raise ValueError(f"packet arg should be `packet.Packet' not '{type(pkt)}'")

        if not self.powered_on:
            pkt.status = "done"
            # nothing more to be done
            return False
        # We would check if it was frozen.  That is a test, not a status.  We do not have that check yet.

        # Deal with DHCP.
        # If it is a request and this is a DHCP server, serve an IP back.
        if pkt.packettype == "DHCP-Request":
            if self.serves_dhcp:
                if self.is_dhcp and "dhcprange" in self.json:
                    session.print(f"Arrived at DHCP server: {self.hostname}")
                    makeDHCPResponse(pkt, self.json, nic)
                    pkt.status = "done"
                    return True
        # If it is a DHCP answer, update the device IP address.
        elif pkt.packettype == "DHCP-Response":
            if pkt.destination_mac == nic.mac and nic.uses_dhcp is True:
                logging.info(
                    f"Recieved DHCP response.  Dealing with it. payload: {pkt.payload}"
                )
                logging.info("packet matches this nic.")
                session.ui.parser.parse(
                    f"set {self.hostname} {nic.name} {pkt.payload.get('ip')}/{pkt.payload.get('subnet')}",
                    False,
                )
                if packet.isEmpty(self.json["gateway"]["ip"]):
                    session.ui.parser.parse(
                        f"set {self.hostname} gateway {pkt.payload.get('gateway')}"
                    )
                pkt.status = "done"
                return True

        # If the packet is destined for here, process that
        # print("Checking destination.  Looking for " + packet.justIP(pkt.destination_ip))
        # print("   Checking against" + str(allIPStrings(thisDevice)))
        if routesPackets(self.json) or deviceHasIP(self.json, pkt.destination_ip):
            # decrement the ttl with every router
            pkt.ttl -= 1
            if pkt.ttl <= 0:
                if pkt.packettype == "traceroute-request":
                    # We need to bounce a response back
                    dest = deviceFromIP(packet.justIP(str(pkt.source_ip)))
                    logging.info(
                        f"A traceroute timed out at {self.hostname}.  Making a return packet"
                    )
                    # we need to generate a traceroute response
                    nPacket = packetFromTo(self.json, dest)
                    nPacket.packettype = "traceroute-response"
                    nPacket.payload = pkt.payload
                    sendPacketOutDevice(nPacket, self.json)
                    nPacket.payload["tempDest"] = nPacket.source_ip
                    nPacket.add_to_packet_list()
                    pkt.status = "done"
                    return True

        if not packet.isEmpty(pkt.destination_ip) and deviceHasIP(
            self.json, pkt.destination_ip
        ):
            pkt.status = "done"
            logging.info(f"Packet '{pkt.packettype}' arrived at destination")

            # ping, send ping packet back
            if pkt.packettype == "ping":
                # logging.debug(f"Test: Returning packet: {pkt.json}")
                # logging.debug(f"Returning packet: {pkt.source_ip} - {packet.justIP(str(pkt.source_ip))}")
                dest = deviceFromIP(packet.justIP(str(pkt.source_ip)))
                # logging.info(f"A ping came.  Making a return packet going to {dest}")

                # we need to generate a ping response
                nPacket = packetFromTo(self.json, dest)
                # logging.debug(f"Created new packet : {dest}")
                nPacket.json["origPingDest"] = deepcopy(pkt.json.get("origPingDest"))
                nPacket.packettype = "ping-response"
                sendPacketOutDevice(nPacket, self.json)
                # logging.debug("new packet sent out of device")
                nPacket.add_to_packet_list()
                # if we are a hub/switch, do not end broadcast pings here; pass them on
                if not forwardsPackets(self.json) and not packet.is_broadcast_mac(
                    pkt.destination_mac
                ):
                    logging.debug("decided packet is finished.  Marking it done")
                    pkt.status = "done"
                    return True
                else:
                    # we continue.  This packet is not stopping here.
                    pkt.status = "good"

            # ping response, mark it as done
            elif pkt.packettype == "ping-response":
                logging.info("Woot! We returned with a ping")
                pkt.status = "done"
                pingsrcip = packet.justIP(pkt.destination_ip)
                srcip = pingdestip = packet.justIP(pkt.source_ip)
                pingdest = deviceFromIP(pingdestip)
                logging.info(f"sourceip is {srcip}")
                logging.info(f"dest host is {pingdest.get('hostname')}")
                # logging.debug(f"Showing orig dest as: {pkt.json.get("origPingDest")}")
                if pkt.health < 100:
                    logging.info(
                        f"Packet was damaged during transit.  Not complete success: Health={pkt.health}"
                    )
                    session.print(
                        f"PING: {pingsrcip} -> {pingdestip}: Partial Success! - Packet damaged in transit.  Health={pkt.health}"
                    )
                else:
                    session.print(f"PING: {pingsrcip} -> {pingdestip}: Success!")
                if pingdest is not None and pkt.health == 100:
                    # deal with broadcast pings.
                    orig_dest = pkt.json.get("origPingDest")
                    if (
                        orig_dest is not None
                        and orig_dest != ""
                        and orig_dest != pkt.destination_ip
                    ):
                        mark_test_as_completed(
                            self.hostname,
                            orig_dest,
                            "SuccessfullyPings",
                            f"Successfully pinged from {self.hostname} to {orig_dest}",
                        )
                        # We mark this as complete too, but the test for 'WithoutLoop' happens later
                        mark_test_as_completed(
                            self.hostname,
                            orig_dest,
                            "SuccessfullyPingsWithoutLoop",
                            f"Successfully pinged from {self.hostname} to {orig_dest} without a network loop.",
                        )

                    mark_test_as_completed(
                        self.hostname,
                        pingdest.get("hostname"),
                        "SuccessfullyPings",
                        f"Successfully pinged from {self.hostname} to {pingdest.get('hostname')}",
                    )
                    # We mark this as complete too, but the test for 'WithoutLoop' happens later
                    mark_test_as_completed(
                        self.hostname,
                        pingdest.get("hostname"),
                        "SuccessfullyPingsWithoutLoop",
                        f"Successfully pinged from {self.hostname} to {pingdest.get('hostname')} without a network loop.",
                    )

                    # print(f" we are done, and packetlist is: {len(session.puzzle.packets)} and storm: {session.packetstorm}")
                return True

            elif pkt.packettype == "traceroute-response":
                # We need to determine what machine responded.  If it was the true dest, we are done.
                # If not, we need to send out a packet with a longer TTL
                pkt.status = "done"
                temp_dest = pkt.payload.get("tempDest")
                if temp_dest is None:
                    return False
                print(
                    f" We are looking at a packet from {temp_dest} and the final destination should be {pkt.payload.get('origDestIP')}"
                )
                if temp_dest != pkt.payload.get("origDestIP"):
                    # It is not the right dest.  Try again
                    sdev = session.puzzle.device_from_name(
                        pkt.payload.get("origSHostname")
                    )
                    ddev = session.puzzle.device_from_name(
                        pkt.payload.get("origDHostname")
                    )
                    print(
                        f"Making new traceroute from {sdev['hostname']} to {ddev['hostname']} with TTL {pkt.payload.get('origTTL') + 1}"
                    )
                    if pkt.payload.get("origTTL") + 1 < 10:
                        traceroute(sdev, ddev, pkt.payload.get("origTTL") + 1)
                else:
                    pingsrcip = packet.justIP(pkt.destination_ip)
                    srcip = pingdestip = packet.justIP(pkt.source_ip)
                    pingdest = deviceFromIP(pingdestip)
                    if pkt.health < 100:
                        logging.info(
                            f"Packet was damaged during transit.  Not complete success: Health={pkt.health}"
                        )
                        session.print(
                            f"PING: {pingsrcip} -> {pingdestip}: Partial Success! - Packet damaged in transit.  Health={pkt.health}"
                        )
                    else:
                        session.print(
                            f"Traceroute: {pingsrcip} -> {pingdestip}: Success!"
                        )
                    if pingdest is not None and pkt.health == 100:
                        mark_test_as_completed(
                            self.hostname,
                            pingdest.get("hostname"),
                            "SuccessfullyTraceroutes",
                            f"Successfully ran traceroute from {self.hostname} to {pingdest.get('hostname')}",
                        )
                return True

        logging.debug(
            f"We made it through.  Now seeing if we need to keep going. {pkt.status}"
        )
        # If the packet is not done and we forward, forward. Basically, a switch/hub
        if (
            pkt.status != "done" or packet.is_broadcast_mac(pkt.destination_mac)
        ) and forwardsPackets(self.json):
            pkt.status = "good"
            send_out_hubswitch(self.json, pkt, nic)
            pkt.status = "done"
            return

        # if the packet is not done and we route, route
        if pkt.status != "done" and routesPackets(self.json):
            # print("routing")
            if not packet.is_broadcast_mac(pkt.destination_mac):
                # we do not route broadcast packets
                sendPacketOutDevice(pkt, self.json)
            else:
                # if it is a broadcast, the packet stops here.
                pkt.status = "done"
            return
        # If we get here, we might have forwarded.  If so, we mark the old packet as done.
        pkt.status = "done"

    # Generic functions
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
            return None  # Never find a mac for this.  Possible many devices would match and it it not a valid IP
        ip = ipaddress.IPv4Address(ip)
        # print ("globalARP: Converting ip: " + str(ip))
    else:
        if packet.isEmpty(str(ip)):
            return None  # Never find a mac for this.  Possible many devices would match and it it not a valid IP
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
            return None  # Never find a destination for this one
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


def getDeviceNicFromLinkNicRec(linkNicRec):
    """
    return the interface that the link connects to
    Args:
    linkNicRec:link-Nic-rec.  This should be link['SrcNic'] or link['DstNic']
    returns: the interface record or None
    """
    # a link nic rec looks like: { "hostid": "100", "nicid": "102", "hostname": "pc0", "nicname": "eth0" }
    tNic = session.puzzle.nic_from_uid(linkNicRec.get("nicid"))
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
            nic = Nic(oneNic)
            localInterface = findLocalNICInterface(destinationIPString, nic)
            if localInterface is not None:
                # We found it.  Use it.
                routeRec["nic"] = nic.json
                routeRec["interface"] = localInterface
                break

    # if not a nic, use the default gateway
    if "gateway" not in routeRec and "nic" not in routeRec:
        # use the device default gateway
        routeRec["gateway"] = theDeviceRec["gateway"]["ip"]

    # if we have a gateway but do not know the nic and interface, find the right one
    if "gateway" in routeRec and "nic" not in routeRec:
        for oneNic in theDeviceRec["nic"]:
            nic = Nic(oneNic)
            localInterface = findLocalNICInterface(routeRec["gateway"], nic)
            if localInterface is not None:
                # We found it.  Use it.
                routeRec["nic"] = nic.json
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
    # tmpval = f"{srcDevice['gateway']['ip']}/{srcDevice['gateway']['mask']}"
    tmpval = f"{srcDevice['gateway']['ip']}"
    GW = ipaddress.ip_address(tmpval)
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
        try:
            device_IP = ipaddress.IPv4Interface(oneIP)
            logging.debug(
                f"checking if device has IP {device_IP.network.broadcast_address} {IPString}"
            )
            if str(device_IP.network.broadcast_address) == str(IPString):
                return True
        except ValueError:
            continue
    return False


def ip_is_broadcast_for_device(deviceRec, ipstr: str):
    """Return True if the specified ipstring is a broadcast IP for any of the interfaces defined on the device"""
    # logging.debug("Checking to see if our device has a broadcast IP")
    if not isinstance(deviceRec["nic"], list):
        # If it is not a list, turn it into a list so we can iterate it
        deviceRec["nic"] = [deviceRec["nic"]]
    for onenic in deviceRec["nic"]:
        # logging.debug(f"    Checking {onenic} {ipstr}")
        nic = Nic(onenic)
        if ip_is_broadcast_for_nic(nic, ipstr):
            # logging.debug("    SUCCESS! It is a broadcast!")
            return True
    return False


def ip_is_broadcast_for_nic(nic, ipstr: str):
    """Return True if the specified ipstring is a broadcast IP for the specified NIC"""
    # logging.debug("Checking to see if our nic has broadcast IP")
    if nic is None:
        return False
    if nic.type[0] == "port":
        return False  # Ports have no IP address
    # loop through all the interfaces and return any that might be local.
    for oneIF in nic.interfaces:
        # logging.debug(f"    Checking {ipstr} with {str(interfaceIP(oneIF))}")
        if packet.isBroadcast(ipstr, str(interfaceIP(oneIF))):
            return True
    return False


def findLocalNICInterface(targetIPstring: str, nic):
    """Return the network interface record that has an IP address that is local to the IP specified as the target
    Args:
        targetIPstring:str - a string IP address, which we are trying to find a local interface for
        nic:nic.Nic - a network card object, which may contain multiple interfaces
    returns: the interface record that is local to the target IP, or None"""
    if nic is None:
        return None
    if nic.type[0] == "port":
        return None  # Ports have no IP address
    # loop through all the interfaces and return any that might be local.
    for oneIF in nic.interfaces:
        if packet.isLocal(targetIPstring, interfaceIP(oneIF)):
            return oneIF
    return None


def findPrimaryNICInterface(nic):
    """return the primary nic interface.  Turns out this is always interface 0"""
    if len(nic.type) > 0:
        return nic.type[0]
    return None


def doInputFromLink(pkt, nic):
    # zero these out.  We will set them below
    pkt.in_host = ""
    pkt.in_interface = ""
    # figure out what device belongs to the nic
    host_id = nic.my_id.host_id
    thisDevice = session.puzzle.device_from_uid(host_id)
    if thisDevice is None:
        raise ValueError(f"Device not found: {host_id}")

    dev = Device(thisDevice)
    pkt.in_host = dev.hostname

    # Do the simple stuff
    if not dev.powered_on or dev.frozen:
        pkt.status = "done"
        # nothing more to be done
        return False

    # If the packet is a DHCP answer, process that here.  To be done later
    # If the packet is a DHCP request, and this is a DHCP server, process that.  To be done later.

    # Find the network interface.  It might be none if the IP does not match, or if it is a switch/hub device.
    tInterface = findLocalNICInterface(pkt.json.get("tdestIP"), nic)
    # if this is None, try the primary interface.
    if tInterface is None:
        tInterface = findPrimaryNICInterface(nic)
    # the interface still might be none if we are a switch/hub port
    # Verify the interface.  This is mainly to work with SSIDs, VLANs, VPNs, etc.
    if tInterface is not None:
        # we track where it came in on.  We do it it here to track vlan info too.
        if isinstance(tInterface, str):
            pkt.in_interface = tInterface
        else:
            pkt.in_interface = tInterface.get("nicname")

        beginIngressOnInterface(pkt, tInterface)

    # the packet status should show dropped or something if we have a problem.
    # but for now, pass it onto the NIC
    # logging.debug(f"We are routing.  Here is the packet: {pkt.json}")
    # logging.debug(f"We are routing.  Here is the nic: {nic.json}")
    pkt.justcreated = False
    return dev.begin_ingress_on_nic(nic, pkt)
    # The NIC passes it onto the device if needed.  We are done with this.


def beginIngressOnInterface(pkt, interfaceRec):
    """Here we would do anything needed to be done with the interface.
    VLAN
    SSID
    Tunnel/VPN
    """
    # right now, we let pass it back
    return True


def send_out_hubswitch(thisDevice, pkt, nic=None):
    # Ensure Packet object.
    if not isinstance(pkt, packet.Packet):
        raise ValueError(f"packet arg should be `packet.Packet' not '{type(pkt)}'")

    # We loop through all nics. (minus the one we came in from)
    onlyport = ""
    if thisDevice.get("mytype") == "net_switch":
        if pkt.destination_mac in thisDevice.get("port_arps", {}):
            # we just send this out the one port.
            onlyport = thisDevice.get("port_arps").get(pkt.destination_mac)

    # print("We are forwarding.")
    for onenic in thisDevice["nic"]:
        n = Nic(onenic)
        # we duplicate the packet and send it out each port-type
        # find the link connected to the port
        # print (f"Should we send out port: {n.name}")
        tlink = n.get_connected_link()
        if tlink is not None and (
            nic is None or nic.uniqueidentifier != n.uniqueidentifier
        ):
            # We have a network wire connected to the NIC.  Send the packet out
            # if it is a switch-port, then we check first if we know where the packet goes - undone
            if onlyport == "" or onlyport == n.name:
                tpacket = packet.Packet(deepcopy(pkt.json))
                # Update location to outgoing link.
                tpacket.packet_location = tlink.get("hostname")
                # Reset distance to the beginning of outgoing link.
                tpacket.distance = 0
                # Set direction.
                if tlink["SrcNic"]["hostname"] == thisDevice.get("hostname"):
                    tpacket.direction = 1  # Src to Dest
                else:
                    tpacket.direction = 2  # Dest to Source
                tpacket.add_to_packet_list()

    # The packet that came in gets killed since it was replicated everywhere else.
    pkt.status = "done"


def makeDHCPResponse(pkt, thisDevice, nic):
    # Ensure Packet object.
    if not isinstance(pkt, packet.Packet):
        raise ValueError(f"packet arg should be `packet.Packet' not '{type(pkt)}'")

    if "dhcplist" not in thisDevice:
        thisDevice["dhcplist"] = {}
    inboundip = nic.interfaces[0]["myip"]["ip"]
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
        # use the starting portion of the range, to allow for broken ranges.
        iparr = iprange["mask"].split(".")
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
    if pkt.source_mac in thisDevice["dhcplist"]:
        # we already have an entry. Use it
        available_ip = thisDevice["dhcplist"][pkt.source_mac]
    else:
        logging.debug(f"DHCP: Making an IP reservation {available_ip} {pkt.source_mac}")

    if available_ip != "":
        # stash it.  if it already exists, we use the same value.
        thisDevice["dhcplist"][pkt.source_mac] = available_ip
        # Now, make a new DHCP response packet
        nPacket = packet.Packet()
        nPacket.source_ip = nic.interfaces[0]["myip"]["ip"]
        nPacket.source_mac = nic.mac
        nPacket.destination_ip = "0.0.0.0"
        nPacket.destination_mac = pkt.source_mac
        nPacket.packettype = "DHCP-Response"
        nPacket.payload = {
            "ip": available_ip,
            "subnet": nic.interfaces[0]["myip"]["mask"],
            "gateway": thisDevice["gateway"]["ip"],
        }
        destlink = nic.get_connected_link()
        nPacket.packet_location = destlink["hostname"]
        if destlink["SrcNic"]["hostname"] == thisDevice["hostname"]:
            nPacket.direction = 1  # Src to Dest
        else:
            nPacket.direction = 2  # Dest to Source
        nPacket.add_to_packet_list()
        logging.info(
            f"Responding to dhcp request.  Assigned IP: {available_ip} to mac {pkt.source_mac}"
        )


def sendPacketOutDevice(pkt, theDevice):
    """Send the packet out of the device."""
    # Ensure Packet object.
    if not isinstance(pkt, packet.Packet):
        raise ValueError(f"packet arg should be `packet.Packet' not '{type(pkt)}'")

    # print("Sending packet out a device: " + theDevice['hostname'])
    # determine which interface/nic we are exiting out of - routing
    pkt.distance = 0  # always reset this
    routeRec = routeRecFromDestIP(theDevice, pkt.destination_ip)
    destlink = None

    # set the source MAC address on the packet as from the nic
    if routeRec is not None:
        logging.debug("Found a route rec.")
        routeRec["nic"] = Nic(routeRec["nic"]).ensure_mac()
        pkt.source_mac = routeRec["nic"]["Mac"]
        pkt.json["tdestIP"] = routeRec.get("gateway")  # track when we use a gateway
        # set the destination MAC to be the GW MAC if the destination is not local
        # this needs an ARP lookup.  That currently is in puzzle, which would make a circular include.
        if (
            pkt.destination_mac != packet.BROADCAST_MAC
            and pkt.packettype != "DHCP-Response"
        ):
            if routeRec.get("gateway") is not None:
                # We are going out the gateway.  Find the ARP for that
                pkt.destination_mac = globalArpLookup(routeRec.get("gateway"))
            else:
                # We are on a local link.  Set the destmac to be the mac of our destination computer
                pkt.destination_mac = globalArpLookup(pkt.destination_ip)

        if routeRec["nic"]["nicname"] == "management_interface0":
            # If we are exiting a switch / hub; we go out the ports
            send_out_hubswitch(theDevice, pkt)
            return
        else:
            # set the packet location being the link associated with the nic
            #   Fail if there is no link on the port
            destlink = Nic(routeRec.get("nic")).get_connected_link()

    if destlink is not None:
        pkt.packet_location = destlink["hostname"]
        if destlink["SrcNic"]["hostname"] == theDevice["hostname"]:
            pkt.direction = 1  # Src to Dest
        else:
            pkt.direction = 2  # Dest to Source
        # If we get here, we know which interface the packet is going out of.
        #track outbound packets.
        ddevice = Device(theDevice)
        #if we are going out the WAN and did not originate here, masq the packet
        #In all other cases, accept
        #valid responses are: masq, accept, drop, reject, none
        if Nic(routeRec["nic"]).type[0] == "wan" and not pkt.justcreated:
            connectionrec = ddevice.AddIPConnectionEntry(pkt.destination_ip, pkt.source_ip, pkt.packettype, 'masq' )
            #here we masquerade the packet
            logging.debug("We are masquerading the packet")
            connectionrec['src'] = Interface(routeRec['interface']).ip_data['ip']
            pkt.source_ip = Interface(routeRec['interface']).ip_data['ip']

        else:
            logging.debug(f"We are tracking outbound packet on {Nic(routeRec["nic"]).type[0]}")
            ddevice.AddIPConnectionEntry(pkt.destination_ip, pkt.source_ip, pkt.packettype, 'accept' )

        # If we are an originating packet, check firewall.  A reply gets allowed.
        if pkt.packettype == "traceroute-response" or pkt.packettype == "ping-response":
            return True

        # This works for originating packets
        if Device(theDevice).AdvFirewallAllows(
            pkt.in_interface, routeRec.get("interface").get("nicname")
        ):
            return True
        else:
            logging.debug(
                f"Packet dropped by firewall: {pkt.in_host} {pkt.in_interface}-{routeRec.get('interface').get('nicname')}"
            )
            session.print("Packet dropped by firewall")
            pkt.status = "done"
            return False

    # If we get here, it did not work.  No route to host.
    # right now, we blow up.  We need to deal with this with a bit more grace.  Passing the error back to the user
    pkt.status = "failed"
    logging.info(
        f"sendpacketoutdevice Giving 'No Route to host' from {theDevice['hostname']} when looking for {pkt.destination_ip}"
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
    if isinstance(dest, str):  # It is a string of an IP.  We should try it.
        dest = ipaddress.IPv4Address(dest)
    # logging.debug(f"We are about to make a packet: {dest} {type(dest)}")
    if isinstance(dest, ipaddress.IPv4Address):
        # This is what we are hoping for; make an empty packet.
        nPacket = packet.Packet()
        nPacket.source_ip = sourceIP(src, dest)
        # The MAC address of the above IP
        nPacket.source_mac = arpLookup(src, nPacket.source_ip)
        # Figure this out
        nPacket.destination_ip = dest  # this should now be the IP
        # If the IP is local, we use the MAC of the host. Otherwise it is the MAC of the gateway,
        nPacket.destination_mac = globalArpLookup(dest)
        if ip_is_broadcast_for_device(src, dest):
            # It is a broadcast, use the broadcast MAC
            logging.debug("It is a broadcast, using broadcast MAC")
            nPacket.destination_mac = packet.BROADCAST_MAC
        nPacket.packettype = ""
        return nPacket


def ping(src, dest):
    """Generate a ping packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
    """
    nPacket = packetFromTo(src, dest)
    if nPacket is None:
        # The problem should have been logged and the user informed in the
        # packetFromTo function; fail silently.
        # logging.error("Failed to create Ping packet.")
        return
    nPacket.packettype = "ping"
    nPacket.justcreated = True
    nPacket.json["origPingDest"] = dest
    sendPacketOutDevice(nPacket, src)
    nPacket.add_to_packet_list()


def traceroute(src, dest, newTTL=1):
    """Generate a traceroute packet, starting at the srcdevice and destined for the destination device
    Args:
        src:srcDevice (also works with a hostname)
        dest:dstDevice (also works with a hostname)
    """
    srchost = ensureHostRec(src)
    desthost = ensureHostRec(dest)
    nPacket = packetFromTo(src, dest)
    nPacket.packettype = "traceroute-request"
    nPacket.justcreated = True
    nPacket.ttl = newTTL  # This is the secret to the traceroute.
    nPacket.payload = {
        "origTTL": newTTL,  # We will increase this as we go out.
        "origSHostname": srchost.hostname,
        "origSourceIP": nPacket.source_ip,
        "origDHostname": desthost.hostname,
        "origDestIP": nPacket.destination_ip,
    }
    logging.info(
        f"Starting traceroute packet from {srchost.hostname} to {desthost.hostname}"
    )
    sendPacketOutDevice(nPacket, src)
    nPacket.add_to_packet_list()


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
            # This NIC can do DHCP.  Send out a request.
            nPacket = packet.Packet()
            # We do not know our IP, so we have no mask to determine.  Broadcast is done using the MAC
            nPacket.source_ip = "255.255.255.255"
            nPacket.source_mac = nic.get("Mac")
            nPacket.destination_ip = "255.255.255.255"
            nPacket.destination_mac = packet.BROADCAST_MAC
            nPacket.packettype = "DHCP-Request"
            sendPacketOutDevice(nPacket, srcDevice)
            nPacket.add_to_packet_list()


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
