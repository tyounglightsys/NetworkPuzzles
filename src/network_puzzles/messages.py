from . import _

puzzles = {
    "0.0": {
        "title": _("Learn how help works"),
        "info": _(
            "*To learn how this program works, first we will acquaint you with the 'Help.' Most of the puzzles you do, you will want to do with as little help as possible. But, there is help when you need it. For this puzzle, choose one of the four help-levels using the slider on the left. Then long-press or mouse-over the PC and see the messages. When you have moused-over for all the buttons (and pressed the ? box), this puzzle will be completed."
        ),
    },
    "0.1": {
        "title": _("Ping Test"),
        "info": _(
            "Select (tap or click) pc0 and ping laptop0 and laptop1. You can enter either the IP address or the hostname of the device you are trying to ping in the pop-up window."
        ),
    },
    "0.1.1": {
        "title": _("Plug in network"),
        "info": _(
            'Plug in the network to the computer that needs it. \n\nSelect the new-item icon (the "+") icon, then select the "link" icon (the line) from the drop-down menu. Select the link\'s first device and NIC, then its second device and NIC.'
        ),
    },
    "0.2": {
        "title": _("No Switch"),
        "info": _(
            'There is no switch. Add one and link the devices to it. \n\nSelect the new-item icon (the "+"), then select the "infrastructure devices" icon from the drop-down menu, then select the switch to add one to the network (make sure you choose a switch and not a hub). Tap or click in an empty space to place the switch, then create links from the switch to each of the computers, choosing which ports to connect.'
        ),
    },
    "0.2.5": {
        "title": _("Power It On"),
        "info": _(
            "The switch is powered off. \n\nSelect it and power it on. Then, ping the laptop from pc0 to make sure things work."
        ),
    },
    "0.3": {
        "title": _("DHCP Request"),
        "info": _(
            "The PC needs to do a DHCP request. \n\nSelect pc0 and tell it to do a DHCP request."
        ),
    },
    "0.3.1": {
        "title": _("IP Puzzle"),
        "info": _(
            'pc0 needs an IP that is local to the other two computers. \n\nSelect pc0 and choose "Edit" from the menu, then select the connected NIC eth0 and give it an appropriate IP Address.'
        ),
    },
    "0.3.4": {
        "title": _("Network Loop"),
        "info": _(
            "This puzzle shows you what happens when there is a network loop. A loop is made when you have your switches connected to themselves or to another one that is connected back to the first one. \n\nPing from pc0 to pc1 to see what happens. You do not need to fix the problem, but removing one of the offending links from one of the switches would do it."
        ),
    },
    "0.3.5": {
        "title": _("Network Loop 2"),
        "info": _(
            "Managed Switches can use Spanning Tree Protocol (STP), which intelligently figures out the least distance path to a point. STP lets you have network loops and survive. \n\nTry pinging pc1 twice from pc0. The first time, some packets are lost. But the second time the packet goes where it should."
        ),
    },
    "0.3.6": {
        "title": _("Frozen!"),
        "info": _(
            "Every once in a while a piece of hardware will freeze up and needs to be rebooted. \n\nTry pinging laptop1 from pc0 and see how the packet fails. It does not get past the switch. Select the switch and power it off, then power it back on. Now try pinging laptop1."
        ),
    },
    "0.4": {
        "title": _("Hub vs Switch"),
        "info": _(
            "This puzzle shows the difference between a hub and a switch. \n\nHave each of the servers ping the computers on the same LAN as themselves, and have those computers ping the server. The switch learns which device is attached to it and only sends the packet to that computer, while the hub sends the packet to every device on the subnet."
        ),
    },
    "0.5": {
        "title": _("Where did I put that?"),
        "info": _(
            'Your boss bought a switch and plugged it into your network, but did not tell you where he put it. Now he wants you to find it. What do you do when you know where something is, but not exactly? You go to the device you know it is plugged into and follow the wire. \n\nTo solve this, drag the switch around, and then find the other end of the wire and "drag" on the empty spot to "find" it. Then, change the IP address of the missing switch.'
        ),
    },
    "0.6": {
        "title": _("Broken Link"),
        "info": _(
            'This shows what happens if there is a broken network wire in your network. \n\nPing laptop1 and see where the packet dies. Open one of the devices connected to that link and you will see that, even though the device has a link connected to it, it does not have a "connection light" saying it is connected.  (The connection-light is the * at the end of the eth name). You can also edit the network card to see if it thinks it is connected. Remove the broken network wire by selecting it and deleting it. Then add the link again. A successful ping tells you if you got it working.'
        ),
    },
    "0.6.5": {
        "title": _("Packet Corruption"),
        "info": _(
            "Network wires that run too close to electrical wires or fluorescent lights can cause packet corruption. \n\nMove the light out of the way if the packet gets corrupted."
        ),
    },
    "0.6.6": {
        "title": _("Packet Corruption2"),
        "info": _(
            "Packets can be partially corrupted by lights. \n\nPing from pc0 to pc1 and look at how the packet goes the first time. Move the light out of the way just a little bit and it should work fine."
        ),
    },
    "0.7": {
        "title": _("Traceroute"),
        "info": _(
            "A traceroute tests the path from one computer to the other. Every routing device along the path will respond (but switches do not). This is done by adding a TTL (Time to Live) number on every packet. Each device that routes packets will subtract one from the TTL. When the TTL reaches zero, the devices will send a response back. Traceroute catches these responses and uses it to determine what each step is along the path.\n\nHave server0 traceroute to server1."
        ),
    },
    "0.10.1": {
        "title": _("Bad Power Supply"),
        "info": _(
            "Occasionally a piece of hardware will break. This often happens after long periods of use, though sometimes after just sitting around unused. This puzzle makes it look a little worse than it usually would look. \n\nGo ahead and turn on the switch. After that, select it and replace it. Things that have been replaced will need to have their settings put back. So make sure to give the new switch a good IP and netmask."
        ),
    },
    "0.10.2": {
        "title": _("Bad Power - Needs UPS"),
        "info": _(
            "Occasionally the electricity in a building, or in a city, has problems. Usually, in these cases, a device will function for a while and then break on you. To make the puzzle go faster, however, we have it break immediately. This puzzle makes it look a little worse than it usually would look. \n\nGo ahead and turn on the switch. After that replace it. If you turn it on again, it will continue to break until you add a UPS to it. After that, it will be fine. Luckily for you, you do not need to pay for the devices you keep replacing! Things that have been replaced will need to have their settings put back, so make sure to give the new switch a good IP and netmask."
        ),
    },
    "1.1": {
        "title": _("Bad IP"),
        "info": _(
            "*PC0 cannot ping one of the other computers. Figure out which one, and change the IP address of that computer so it works."
        ),
    },
    "1.2": {
        "title": _("Bad DHCP"),
        "info": _(
            "*The Server is giving out bad DHCP. Edit the DHCP settings to tell it to give correct DHCP.  (You do this by selecting 'DHCP' from the device-editing screen) Then do a DHCP request on all the PCs."
        ),
    },
    "1.3": {
        "title": _("Gateway Puzzle"),
        "info": _(
            "*The items on one network cannot ping the items on the other network (separated by the router). Figure why and fix it. All computers and switches need fixing, but the router is OK."
        ),
    },
    "1.4": {
        "title": _("Duplicate IPs"),
        "info": _("Get the PCs so they are happy"),
    },
    "1.4.1": {
        "title": _("Two Subnets, Shared Network"),
        "info": _(
            "*This network has two different subnets using the same switch. Ping from the different PCs to machines on the other network.\nThis is a two-part network; you will see this same network again in the next puzzle, but using one router instead of two. We will use these concepts later on, when we are dealing with security."
        ),
    },
    "1.4.2": {
        "title": _("Two Subnets, Shared Network2"),
        "info": _(
            "*This network has two different subnets using the same switch. The router has two interfaces (IP addresses, both on eth0). One network card functions like two. Ping from the different PCs to machines on the other network.\nThis is the same network as the previous one, except it uses one router instead of two. We will be using this concept later on when we talk about security. The reason we will use it, is that we may want to have different groups of people on a network (maybe students, faculty, and guests), and we want to have different security levels for each group. By having student traffic need to go through one router before it gets to the staff network, we can set up firewall rules to block students from accessing faculty data. But, that is for a later puzzle."
        ),
    },
    "1.4.3": {
        "title": _("Adding Devices"),
        "info": _(
            "*This puzzle has three tasks to it:\n1) Give the switch an IP address\n2) Add an IP-Phone to the network, linking it to the switch, and then do a DHCP request for it.\n3) Ping the switch from the IP-Phone"
        ),
    },
    "1.5": {
        "title": _("Add DHCP Server"),
        "info": _(
            "*These IP-Phones cannot have a static IP. You must add a server on the 192.168.1.0 network and configure the DHCP server. Give an IP to the phone, so the phone can ping the PCs on the other side of the network"
        ),
    },
    "1.6": {
        "title": _("Bad Gateway"),
        "info": _(
            "*Computers can only communicate with other computers that are local to them. Gateways must have an IP address that is local to the client. Ping pc0 from pc1 and see if you can spot the error."
        ),
    },
    "1.7": {
        "title": _("Duplicate MAC addresses"),
        "info": _(
            "*This puzzle shows you what happens when there are duplicate MAC addresses. This rarely happens, but it used to happen more often than should be statistically probable. Cheap network card vendors used to make batches of cards with the same MAC address, and occasionally someone would buy two of them. The best solution is to replace one of the NICs that has the duplicate MAC address. Ping both pc0 and pc1 from pc2."
        ),
    },
    "1.9.7": {
        "title": _("Bad Netmask"),
        "info": _(
            '*One of the subnets has a poorly crafted subnet. There are two ways to represent subnets. The "dot-decimal" notation (255.255.255.0) and CIDR (/24). \n\nHere, we are using a subnet of 255.255.255.129. The 129, in binary, is 10000001. That trailing 1 is the problem. It basically puts the odd numbers in one subnet and the even numbers in the other subnet. While it is possible to get networks to function with a terrible subnet mask like this, do not do it. Use numbers that are properly represented by CIDR notation. Basically, in binary, you want a bunch of 1s, followed by 0s.  (111000), not 1s and 0s intermingled.  (10101). CIDR (/25) represents the number of 1s, and the rest are 0.\n\nTo solve this puzzle, find the IP Addresses that have the /? and change the subnet to something that works. Then, try pinging.'
        ),
    },
    "1.21": {
        "title": _("Practice1"),
        "info": "",
    },
    "1.22": {
        "title": _("Practice2"),
        "info": "",
    },
    "1.23": {
        "title": _("Practice3"),
        "info": "",
    },
    "1.24": {
        "title": _("Practice4"),
        "info": "",
    },
    "1.25": {
        "title": _("Practice5"),
        "info": "",
    },
    "1.26": {
        "title": _("Practice6"),
        "info": "",
    },
    "1.27": {
        "title": _("Practice7"),
        "info": "",
    },
}

# ref:
# - https://git.solidcharity.com/timy/EduNetworkBuilder/src/branch/master/EduNetworkBuilder/NetTest.cs
# - https://git.solidcharity.com/timy/EduNetworkBuilder/src/branch/master/EduNetworkBuilder/Resources/languages/edustrings.resx
nettests = {
    "DeviceBlowsUpWithPower": {
        "basic": _("has a problem"),
        "hints": _("hardware problem"),
        "full": _("bad power supply"),
    },
    "DeviceIsFrozen": {
        "basic": _("has a problem"),
        "hints": _("device is frozen"),
        "full": _("reboot the device"),
    },
    "DeviceNeedsUPS": {
        "basic": _("has a problem"),
        "hints": _("is plugged into bad power"),
        "full": _("needs a UPS"),
    },
    "DeviceNICSprays": {
        "basic": _("has a problem"),
        "hints": _("network card sprays net when used"),
        "full": _("network card sprays net when used"),
    },
    "DHCPServerEnabled": {
        "basic": _("has a problem"),
        "hints": _("needs change to DHCP server:"),
        "full": _("DHCP server enabled ="),
    },
    "FailedPing": {
        "basic": _("has a problem"),
        "hints": _("should fail to ping a specific host"),
        "full": _("needs to try to ping (and fail):"),
    },
    "HelpRequest": {
        "basic": _("has a problem"),
        "hints": _("get mouse-over help"),
        "full": _("get mouse-over help of level:"),
    },
    "LockAll": {
        "basic": _("has a problem"),
        "hints": _("is locked"),
        "full": _("is locked:"),
    },
    "LockDHCP": {
        "basic": _("has a problem"),
        "hints": _("has locked DHCP"),
        "full": _("has locked DHCP:"),
    },
    "LockGateway": {
        "basic": _("has a problem"),
        "hints": _("has locked gateway"),
        "full": _("has locked gateway:"),
    },
    "LockInterfaceVLAN": {
        "basic": _("has a problem"),
        "hints": _("the VLAN on an interface is locked"),
        "full": _("the VLAN on an interface is locked:"),
    },
    "LockIP": {
        "basic": _("has a problem"),
        "hints": _("has locked IP"),
        "full": _("has locked IP:"),
    },
    "LockLocation": {
        "basic": _("has a problem"),
        "hints": _("device cannot be moved"),
        "full": _("device cannot be moved:"),
    },
    "LockNic": {
        "basic": _("has a problem"),
        "hints": _("has locked NIC"),
        "full": _("has locked NIC:"),
    },
    "LockNicVLAN": {
        "basic": _("has a problem"),
        "hints": _("the VLAN on a NIC is locked"),
        "full": _("the VLAN on a NIC is locked:"),
    },
    "LockRoute": {
        "basic": _("has a problem"),
        "hints": _("has locked route"),
        "full": _("has locked route:"),
    },
    "LockVLANNames": {
        "basic": _("has a problem"),
        "hints": _("VLAN names and IDs are locked"),
        "full": _("VLAN names and IDs are locked:"),
    },
    "LockVLANsOnHost": {
        "basic": _("has a problem"),
        "hints": _("a VLAN is locked"),
        "full": _("a VLAN is locked:"),
    },
    "NeedsDefaultGW": {
        "basic": _("has a problem"),
        "hints": _("needs the gateway set"),
        "full": _("needs the gateway set to:"),
    },
    "NeedsForbiddenVLAN": {
        "basic": _("has a problem"),
        "hints": _("the interface needs a forbidden VLAN"),
        "full": _("the interface needs a forbidden VLAN:"),
    },
    "NeedsLinkToDevice": {
        "basic": _("has a problem"),
        "hints": _("needs to be connected to the network"),
        "full": _("needs a link to host:"),
    },
    "NeedsLocalIPTo": {
        "basic": _("has a problem"),
        "hints": _("needs a local IP"),
        "full": _("needs an IP local to host:"),
    },
    "NeedsPingToHost": {
        "basic": _("has a problem"),
        "hints": _("cannot ping"),
        "full": _("cannot ping host:"),
    },
    "NeedsRouteToNet": {
        "basic": _("has a problem"),
        "hints": _("needs a route set"),
        "full": _("needs a route to network:"),
    },
    "NeedsTaggedVLAN": {
        "basic": _("has a problem"),
        "hints": _("the interface needs a tagged VLAN"),
        "full": _("the interface needs a tagged VLAN:"),
    },
    "NeedsUntaggedVLAN": {
        "basic": _("has a problem"),
        "hints": _("the interface needs an untagged VLAN"),
        "full": _("the interface needs an untagged VLAN:"),
    },
    "ReadContextHelp": {
        "basic": _("has a problem"),
        "hints": _("read context help for:"),
        "full": _("read context help for:"),
    },
    "SuccessfullyArps": {
        "basic": _("has a problem"),
        "hints": _("needs to find ARP from some device"),
        "full": _("needs to find ARP from:"),
    },
    "SuccessfullyDHCPs": {
        "basic": _("has a problem"),
        "hints": _("needs a DHCP IP address"),
        "full": _("needs a DHCP IP address from server:"),
    },
    "SuccessfullyPings": {
        "basic": _("has a problem"),
        "hints": _("must ping a host"),
        "full": _("must ping:"),
    },
    "SuccessfullyPingsAgain": {
        "basic": _("has a problem"),
        "hints": _("must ping a host"),
        "full": _("must ping:"),
    },
    "SuccessfullyPingsWithoutLoop": {
        "basic": _("has a problem"),
        "hints": _("must ping a host"),
        "full": _("must ping:"),
    },
    "SuccessfullyTraceroutes": {
        "basic": _("has a problem"),
        "hints": _("needs to traceroute"),
        "full": _("needs to traceroute to:"),
    },
}
