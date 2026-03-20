import logging
import random

from . import interface, packet, session
from .core import ItemBase
from .link import Link


class Nic(ItemBase):
    def __init__(self, json_data=None, device=None):
        super().__init__(json_data)
        self._can_use_dhcp = None
        self._device = device

    def __str__(self):
        return self.name

    @property
    def can_use_dhcp(self):
        if self._can_use_dhcp is None:
            if self.type in ("eth", "management_interface", "wlan"):
                self._can_use_dhcp = True
            else:
                self._can_use_dhcp = False
        return self._can_use_dhcp

    @can_use_dhcp.setter
    def can_use_dhcp(self, value):
        self._can_use_dhcp = value

    @property
    def device(self):
        if self._device is None:
            self._device = session.puzzle.device_from_uid(self.my_id.host_id)
        return self._device

    # @device.setter
    # def device(self, value):
    #     """Define device JSON data; accepts JSON or hostid"""
    #     if isinstance(value, dict):
    #         self._device = value
    #     elif isinstance(value, str):
    #         self._device = session.puzzle.device_from_uid(value)

    @property
    def interfaces(self):
        if not isinstance(self.json.get("interface"), list):
            self.json["interface"] = [self.json.get("interface")]
        return self.json.get("interface")

    @property
    def ip_addresses(self):
        ips = list()
        for iface_data in self.interfaces:
            iface = interface.Interface(iface_data)
            if iface.nicname == self.name:
                ip_addr = interface.IpAddress(iface.ip_data)
                if not ip_addr.address.startswith("0"):
                    ips.append(iface.ip_data)
                break
        return ips

    @property
    def mac(self):
        return self.json.get("Mac")

    @property
    def my_id(self):
        """Object with "myid" data."""
        return MyId(self.json.get("myid"))

    @property
    def name(self):
        return self.json.get("nicname", "")

    @name.setter
    def name(self, value):
        self.json["nicname"] = value

    @property
    def type(self):
        # NOTE: The JSON data defines nictype as a list of two identical
        # strings. We simply return the first one.
        if self.json.get("nictype") is None:
            self.type = ""
        return self.json.get("nictype")[0]

    @type.setter
    def type(self, value):
        self.json["nictype"] = [value, value]

    @property
    def uniqueidentifier(self):
        return self.json.get("uniqueidentifier", "")

    @property
    def encryption_key(self):
        if self.json.get("encryptionkey") is None:
            # Some JSON files have this set as `null`, which translates to
            # `None`, but we need a string for GUI use.
            self.json["encryptionkey"] = ""
        return self.json.get("encryptionkey", "")

    @encryption_key.setter
    def encryption_key(self, value: str):
        # Key can't contain "," because parser replaces "," with " " during
        # tokenization.
        if "," in value:
            raise ValueError("Invalid character: ,")
        self.json["encryptionkey"] = value

    @property
    def ssid(self):
        return self.json.get("ssid", "")

    @ssid.setter
    def ssid(self, value: str):
        self.json["ssid"] = value

    @property
    def endpoint(self):
        return self.tunnel_endpoint.get("ip", "")

    @endpoint.setter
    def endpoint(self, value: str):
        self.tunnel_endpoint["ip"] = value

    @property
    def tunnel_endpoint(self):
        if self.json.get("tunnelendpoint") is None:
            self.json["tunnelendpoint"] = {}
        return self.json.get("tunnelendpoint")

    @property
    def uses_dhcp(self):
        if self.json.get("usesdhcp") is None:
            self.json["usesdhcp"] = "false"
        return self.json.get("usesdhcp").lower() in ["true", "yes"]

    @uses_dhcp.setter
    def uses_dhcp(self, value):
        if isinstance(value, bool):
            value = str(value)
        self.json["usesdhcp"] = value

    def begin_ingress(self, pkt, dev):
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
        if self.type in ("port", "wport"):
            trackPackets = True
        if dev.is_wireless_forwarder and self.type == "wlan":
            trackPackets = True

        if self.type == "port" and dev.mytype == "wap":
            trackPackets = True
        if trackPackets:
            # We need to track ARP.  Saying, this MAC address is on this port. Simulates STP (Spanning Tree Protocol)
            if "port_arps" not in dev.json:
                dev.json["port_arps"] = {}
            if pkt.source_mac not in dev.json.get("port_arps"):
                dev.json["port_arps"][pkt.source_mac] = self.name

        # Look better tracking for network loops
        # If the same packet hits the same switch, we determine it is a loop
        # Check if the hostname is already in the path of the packet.  If so, it is a loop
        if dev.hostname in pkt.path:
            session.packetstorm = True
        pkt.path.append(dev.hostname)

        # If we are entering a WAN port, see if we should be blocked or if it is a return packet
        if self.type == "vpn":
            logging.debug(f"Coming in a VPN link: {pkt.json}")
        if self.type == "wan":
            connection_info = dev.ReturnIPConnectionEntry(
                pkt.destination_ip, pkt.source_ip, pkt.packettype
            )
            if connection_info is not None:
                logging.debug(f"Found a return packet: {connection_info}")
                if connection_info["response"] == "masq":
                    logging.debug(
                        f"Packet was masqueraded.  Switching it back {connection_info['src']} -> {connection_info['masqsrc']}"
                    )
                    pkt.destination_ip = connection_info["masqsrc"]
            else:
                # we do not have a record of this.  Packets coming into the WAN, unless it is destined for here, are dropped.
                # see if the packet is destined for us.
                t_nic = dev.nic_from_ip(pkt.destination_ip)
                if t_nic is None:
                    logging.debug(
                        "No record of this and not destined for this machine.  Drop it for now"
                    )
                    pkt.status = "done"
                    return False
        if pkt.destination_mac is None:
            # The packet was improperly crafted or no such machine exists.  Drop
            logging.debug(
                "This packet was killed.  There was a problem.  No such destination.  No MAC Address that matched"
            )
            pkt.status = "failed"
            return False

        if (
            pkt.destination_mac == self.mac
            or packet.is_broadcast_mac(pkt.destination_mac)
            or dev.routes_packets
            or dev.is_wireless_forwarder
            or self.type == "port"
            or self.type == "wport"
        ):
            # The packet is good, and has reached the computer.  Pass it on to the device
            logging.debug(f"Packet entering device: {dev.hostname}")
            return dev.receive_packet(pkt, self)
        else:
            logging.info("packet did not match.  Dropping")
            logging.info(
                f"  packet dst MAC {pkt.destination_mac} ({dev.hostname}) vs this NIC  {self.mac}"
            )
            pkt.status = "dropped"
            return False

    def ensure_mac(self, data=None):
        if data is not None:
            new_data = data
        else:
            new_data = self.json

        if "Mac" not in new_data:
            # Most of the network cards do not have this done yet.  We generate a new random one
            localmac = ""
            for i in range(1, 13):
                localmac = localmac + random.choice("ABCDEF1234567890")
            new_data["Mac"] = localmac

        self.json = new_data
        return new_data

    def find_local_interface(self, targetIPstring: str, skip_zeros=False):
        """Return the network interface record that has an IP address that is local to the IP specified as the target
        Args:
            targetIPstring:str - a string IP address, which we are trying to find a local interface for
            nic:nic.Nic - a network card object, which may contain multiple interfaces
        returns: the interface record that is local to the target IP, or None"""

        if self.type == "port":
            return None  # Ports have no IP address

        # loop through all the interfaces and return any that might be local.
        for oneIF in self.interfaces:
            iface_address = str(interface.Interface(oneIF).ipaddress)
            if skip_zeros and iface_address == "0.0.0.0/0":
                logging.debug("Found 0.0.0.0.  skipping")
                continue
            if packet.isLocal(targetIPstring, iface_address):
                return oneIF
        return None

    def find_primary_interface(self):
        """Return the primary NIC interface. Turns out this is always interface 0"""
        # NOTE: Nic.type returns None if not set.
        return self.type

    def get_connected_link(self):
        """Find a link connected to the specified network card"""
        # logging.debug(
        #    f"looking for link connected to nic; #{self.my_id.nic_id}; {self.name}"
        # )
        for one in session.puzzle.links:
            if one:
                # print ("   link - " + one['hostname'])
                if one["SrcNic"]["nicid"] == self.my_id.nic_id:
                    return one
                if one["DstNic"]["nicid"] == self.my_id.nic_id:
                    return one
        # we did not find anything that matched.  Return None
        return None

    def is_connected(self):
        """Connected status of given interface.
        returns: boolean
        """
        for link_data in session.puzzle.links:
            link = Link(link_data)
            # Check if NIC is used by host device as src or dest.
            if self.my_id.hostname == link.src and self.name == link.src_nic.get(
                "nicname"
            ):  # NIC used as link src
                if link.linktype == "broken":
                    return False
                else:
                    return True
            if self.my_id.hostname == link.dest and self.name == link.dest_nic.get(
                "nicname"
            ):  # NIC used as link dest
                if link.linktype == "broken":
                    return False
                else:
                    return True
        return False

    def receive_packet(self, pkt, dev):
        # Zero this out. We will set it below.
        pkt.in_interface = ""

        # If the packet is a DHCP answer, process that here.  To be done later
        # If the packet is a DHCP request, and this is a DHCP server, process that.  To be done later.

        # Find the network interface.  It might be none if the IP does not match, or if it is a switch/hub device.
        tInterface = self.find_local_interface(pkt.json.get("tdestIP"))
        # if this is None, try the primary interface, which is always Nic.type.
        if tInterface is None:
            tInterface = self.find_primary_interface()
        # the interface still might be none if we are a switch/hub port
        # Verify the interface.  This is mainly to work with SSIDs, VLANs, VPNs, etc.
        if tInterface is not None:
            # we track where it came in on.  We do it it here to track vlan info too.
            if isinstance(tInterface, str):
                pkt.in_interface = tInterface
            else:
                pkt.in_interface = tInterface.get("nicname")
            logging.debug(f"Beginning on interface: {tInterface}")
            # FIXME: if tInterface is "primary interface", it will only be a str
            # rather than JSON data, which will cause a ValueError here. But
            # since this currently always returns True, we'll just skip it for
            # now.
            # interface.Interface(tInterface).begin_ingress(pkt)

        # the packet status should show dropped or something if we have a problem.
        # but for now, pass it onto the NIC
        # logging.debug(f"We are routing.  Here is the packet: {pkt.json}")
        # logging.debug(f"We are routing.  Here is the nic: {nic.json}")
        pkt.justcreated = False
        logging.debug(f"Beginning on nic: {self.name}")
        return self.begin_ingress(pkt, dev)
        # The NIC passes it onto the device if needed.  We are done with this.


class MyId(ItemBase):
    """Helper class for accessing NIC "myid" data."""

    def __init__(self, json_data=None):
        super().__init__(json_data)

    @property
    def host_id(self):
        return self.json.get("hostid")

    @property
    def hostname(self):
        return self.json.get("hostname")

    @property
    def nic_id(self):
        return self.json.get("nicid")

    @property
    def nicname(self):
        return self.json.get("nicname")
