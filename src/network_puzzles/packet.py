import ipaddress
import logging
import re
import time
from copy import deepcopy

from . import device, session
from .core import ItemBase
from .link import Link
from .nic import Nic

BROADCAST_MAC = "FFFFFFFFFFFF"


class Packet(ItemBase):
    EMPTY_PACKET_JSON = {
        "packettype": "",
        "VLANID": 0,  # start on the default vlan
        "health": 100,  # health.  This will drop as the packet goes too close to things causing interferance
        "sourceIP": "",
        "TTL": 32,  # The initial time-to-live.  This is really only needed for traceroute packets
        "sourceMAC": "",
        "destIP": "",
        "destMAC": "",
        "tdestIP": "",  # If we are going through a router.  Mainly so we know which interface we are supposed to be using
        "status": "good",
        "statusmessage": "",
        "payload": "",
        "packetlocation": "",  # where the packet is.  Should almost always be a link name
        "packetDirection": 0,  # Which direction are we going on a network link.  1=src to dest, 2=dest to src
        "packetDistance": 0,  # The % distance the packet has traversed.  This is incremented until it reaches 100%
    }

    def __init__(self, json_data=None):
        if json_data is None:
            # deepcopy keeps class attribute from being changed.
            json_data = deepcopy(self.EMPTY_PACKET_JSON)
            # Seconds since epoc. Failsafe that will kill the packet if too much time has passed
            json_data["starttime"] = int(time.time() * 1000)
        super().__init__(json_data)
        self.session = session
        # TODO: Consider adding packet data to puzzle JSON for comprehensive tracking.
        # If this is done, then json_data should be copied before instantiating
        # this class rather than being copied here.
        # if self.session.puzzle:
        #     self.session.puzzle.add_packet(self.json)
        self.damage_count = 0
        self.health_init = self.health

    @property
    def destination_ip(self):
        return self.json.get("destIP")

    @destination_ip.setter
    def destination_ip(self, value):
        self.json["destIP"] = value

    @property
    def destination_mac(self):
        return self.json.get("destMAC")

    @destination_mac.setter
    def destination_mac(self, value):
        self.json["destMAC"] = value

    @property
    def direction(self) -> int | None:
        return self.json.get("packetDirection")

    @direction.setter
    def direction(self, value):
        value = int(value)  # ensure int
        self.json["packetDirection"] = value

    @property
    def distance(self):
        return self.json.get("packetDistance")

    @distance.setter
    def distance(self, value):
        self.json["packetDistance"] = value

    @property
    def hash_id(self):
        """Get unique identifier by hashing specific properties of packet data."""
        return hash(
            (
                self.source_ip,
                self.source_mac,
                self.destination_ip,
                self.destination_mac,
                self.packet_location,
            )
        )

    @property
    def health(self):
        return self.json.get("health")

    @health.setter
    def health(self, value):
        self.json["health"] = value

    @property
    def packet_location(self):
        return self.json.get("packetlocation", "")

    @packet_location.setter
    def packet_location(self, value):
        self.json["packetlocation"] = value

    @property
    def packettype(self):
        return self.json.get("packettype")

    @packettype.setter
    def packettype(self, value):
        if not isinstance(value, str):
            raise ValueError(f"Invalid type for `packettype`: {type(value)}")
        self.json["packettype"] = value

    @property
    def path(self):
        if self.json.get("path") is None:
            self.json["path"] = []
        return self.json.get("path")

    @property
    def payload(self):
        return self.json.get("payload")

    @payload.setter
    def payload(self, value):
        if not isinstance(value, dict):
            raise ValueError(f"Invalid type for payload: {type(value)}")
        self.json["payload"] = value

    @property
    def source_ip(self):
        return self.json.get("sourceIP")

    @source_ip.setter
    def source_ip(self, value):
        self.json["sourceIP"] = value

    @property
    def source_mac(self):
        return self.json.get("sourceMAC")

    @source_mac.setter
    def source_mac(self, value):
        self.json["sourceMAC"] = value

    @property
    def starttime(self):
        return self.json.get("starttime")

    @property
    def status(self):
        return self.json.get("status", "")

    @status.setter
    def status(self, value):
        if not isinstance(value, str):
            raise ValueError(f"Invalid type for status: {type(value)}")
        self.json["status"] = value

    @property
    def statusmessage(self):
        return self.json.get("statusmessage", "")

    @statusmessage.setter
    def statusmessage(self, value):
        self.json["statusmessage"] = str(value)

    def add_to_packet_list(self):
        """Convenience function for managing packets."""
        self.session.puzzle.packets.append(self)

    def remove_from_packet_list(self):
        """Convenience function for managing packets."""
        self.session.puzzle.packets.remove(self)

    def apply_possible_damage(self, tick_pct):
        """Damage the packet if near enough to microwave (wireless connection) or light (wired connection)."""
        # Find link that packet is traveling on.
        lnk = self.get_current_link()
        if lnk is None:
            logging.warning(
                f"Unable to apply damage because no `Link` found for `Packet`: {self.json}"
            )
            return

        # List damage-causing devices in puzzle.
        risky_devices = []
        for dev_json in self.session.puzzle.devices:
            dev = device.Device(dev_json)
            if dev.mytype == "microwave" and lnk.linktype == "wireless":
                risky_devices.append(dev)
            if dev.mytype == "fluorescent" and lnk.linktype != "wireless":
                risky_devices.append(dev)

        # Check if each device is close enough to damage packet.
        for dev in risky_devices:
            # We need to check for damage.
            dx, dy = dev.location
            # calculate the centerpoint
            halfsize = int(
                dev.size / 2
            )  # all devices in EduNetworkBuilder were 100 size
            dx += halfsize
            dy += halfsize

            # Now compare locations to each point along the distance.
            for px, py in self.get_distance_points(tick_pct):
                # NOTE: It seems unnecessary (or possibly erroneous) to
                # convert the distance() value below into an int, because
                # this would theoretically apply damage even when the
                # distance between the objects is just beyond the threshold
                # but happens to round down (when using int()) to the
                # threshold. However, changing this conversion might have
                # unintended consequences on already-designed puzzles. so it
                # has been left as an int accordingly.
                # Compare distance between device and packet with threshold.
                if int(distance(px, py, dx, dy)) <= 43:
                    self.health -= 1
                    self.damage_count += 1
                    if self.health <= 0:
                        self.status = "done"  # the packet dies silently
            if self.health_init > self.health:
                logging.debug(f"Packet damaged: {self.packettype} {self.health}")

    def get_distance_points(self, tick_pct):
        devices = self.get_current_link_endpoint_devices()
        if devices is None or not isinstance(devices, tuple):
            return None
        src_device, dest_device = devices
        sx, sy = src_device.location
        dx, dy = dest_device.location
        # We now have a line that the packet is somewhere on; calculate progress.
        deltax = (dx - sx) / 100
        deltay = (dy - sy) / 100

        points = list()
        for a in range(int(self.distance), int(self.distance + tick_pct), 2):
            tx = sx + (deltax * a)
            ty = sy + (deltay * a)
            points.append([tx, ty])
        return points

    def get_current_link(self) -> Link | None:
        link_data = self.session.puzzle.link_from_name(self.packet_location)
        if link_data is None:
            return None  # We could not find the link
        return Link(link_data)

    def get_current_link_endpoint_devices(self):
        """Return tuple of (src_device, dest_device)."""
        src_nic, dest_nic = self.get_current_link_endpoint_nics()
        src_json = self.session.puzzle.device_from_uid(src_nic.my_id.host_id)
        dest_json = self.session.puzzle.device_from_uid(dest_nic.my_id.host_id)
        if None in (src_json, dest_json):
            return None
        return (device.Device(value=src_json), device.Device(value=dest_json))

    def get_current_link_endpoint_nics(self):
        """Return tuple of (SrcNic, DstNic)."""
        current_link = self.get_current_link()
        src_nic_myid = current_link.src_nic
        dest_nic_myid = current_link.dest_nic
        if self.direction == 1:
            dest_nic_myid = current_link.src_nic
            src_nic_myid = current_link.dest_nic
        src_nic_data = device.getDeviceNicFromLinkNicRec(src_nic_myid)
        dest_nic_data = device.getDeviceNicFromLinkNicRec(dest_nic_myid)
        return (Nic(src_nic_data), Nic(dest_nic_data))


def distance(sx, sy, dx, dy):
    # we have a 5/5 grid that we are working with.
    # The ** is the exponent.  **2 is squared, **.5 is the square-root
    return ((((sx - dx) ** 2) + ((sy - dy) ** 2)) ** 0.5) / 5


def is_ipv6(string):
    """
    return True if the string is a valid IPv4 address.
    """
    try:
        ipaddress.IPv6Network(string)
        return True
    except ValueError:
        return False


def is_ipv4(string):
    """
    return True if the string is a valid IPv4 address.
    """
    try:
        ipaddress.IPv4Network(string)
        return True
    except ValueError:
        return False


def justIP(ip):
    """return just the IP address as a string, stripping the subnet if there was one"""
    if not isinstance(ip, str):
        ip = str(ip)  # change it to a string
    ip = re.sub("/.*", "", ip)
    return ip


def get_ip_range(start_ip, end_ip):
    """
    Generates a list of IP addresses between a start and end IP address (inclusive).
    """
    try:
        start = ipaddress.IPv4Address(start_ip)
        end = ipaddress.IPv4Address(end_ip)
    except ipaddress.AddressValueError:
        session.print("Invalid IP address format.")
        return []

    if start > end:
        session.print("Start IP address must be less than or equal to End IP address.")
        return []

    ip_list = []
    current_ip = start
    while current_ip <= end:
        ip_list.append(str(current_ip))
        current_ip += 1
    return ip_list


def isLocal(packetIP: str, interfaceIP: str):
    """Determine if the packet IP is considered local by the subnet/netmask on the interface IP
    Args:
        packetIP:str - a string IP (ipv6/ipv4); just an IP - no subnet
        interfaceIP:str - an IP/subnet, either iPv4 or ipv6"""
    t_packetIP = justIP(packetIP)
    try:
        ip = ipaddress.ip_address(t_packetIP)
        network = ipaddress.ip_network(
            interfaceIP, strict=False
        )  # The interface will have host bits set, so we choose false
        return ip in network
    except ValueError:
        # Handle invalid IP address or subnet format
        return False


def isBroadcast(packetIP: str, interfaceIP: str):
    """Determine if the packet IP is considered broadcast by the subnet/netmask on the interface IP
    Args:
        packetIP:str - a string IP (ipv6/ipv4); just an IP - no subnet
        interfaceIP:str - an IP/subnet, either iPv4 or ipv6"""
    t_packetIP = justIP(packetIP)
    try:
        ip = ipaddress.ip_address(t_packetIP)
        network = ipaddress.ip_network(
            interfaceIP, strict=False
        )  # The interface will have host bits set, so we choose false
        logging.debug(f" Checking packet: {str(ip)} {str(network.broadcast_address)}")
        return str(ip) == str(network.broadcast_address)
    except ValueError:
        # Handle invalid IP address or subnet format
        return False


def is_broadcast_mac(mac: str):
    """Check to see if the mac address is the broadcast one. Should be FFFFFFFFFFFF"""
    return mac.replace(":", "").replace("-", "").upper() == BROADCAST_MAC


def isEmpty(iptocheck: str):
    # logging.debug(f"Checking if empty: {iptocheck} type of variable {type(iptocheck)}")
    if isinstance(iptocheck, str) and justIP(iptocheck) == "0.0.0.0":
        logging.debug("  Is empty")
        return True
    if isinstance(iptocheck, ipaddress.IPv4Address) and (
        iptocheck == ipaddress.IPv4Interface("0.0.0.0/0")
        or iptocheck == ipaddress.IPv4Address("0.0.0.0")
    ):
        # logging.debug("  Is empty")
        return True
    # logging.debug("  Not empty")
    return False
