# from . import _

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
            "Tap or click pc0 and ping laptop0 and laptop1. You can enter either the IP address or the hostname of the device you are trying to ping in the pop-up window."
        ),
    },
    "0.1.1": {
        "title": _("Plug in network"),
        "info": _(
            'Plug in the network to the computer that needs it. \n\nTap or click the new-item icon (the "+") icon, then select the "link" icon (the line) from the drop-down menu. Select the link\'s first device and NIC, then its second device and NIC.'
        ),
    },
    "0.2": {
        "title": _("No Switch"),
        "info": _(
            'There is no switch. Add one and link the devices to it. \n\nTap or click the new-item icon (the "+"), then select the "infrastructure devices" icon from the drop-down menu, then select the switch to add one to the network (make sure you choose a switch and not a hub). Tap or click in an empty space to place the switch, then create links from the switch to each of the computers, choosing which ports to connect.'
        ),
    },
    "0.2.5": {
        "title": _("Power It On"),
        "info": _(
            "The switch is powered off. \n\nTap or click it and power it on. Then, ping the laptop from pc0 to make sure things work."
        ),
    },
    "0.3": {
        "title": _("DHCP Request"),
        "info": _(
            "The PC needs to do a DHCP request. \n\nTap or click pc0 and tell it to do a DHCP request."
        ),
    },
    "0.3.1": {
        "title": _("IP Puzzle"),
        "info": _(
            'pc0 needs an IP that is local to the other two computers. \n\nTap or click pc0 and choose "Edit" from the menu, then select the connected NIC eth0 and give it an appropriate IP Address.'
        ),
    },
    "0.3.4": {
        "title": _("Network Loop"),
        "info": _(
            "This puzzle shows you what happens when there is a network loop. A loop is made when you have your switches connected to themselves or to another one that is connected back to the first one. \n\nPing from pc0 to pc1 to see what happens. You do not need to fix the problem, but removing one of the offending links from one of the switches would do it."
        ),
    },
    "0.3.5.1": {
        "title": _("Network Loop 2"),
        "info": _(
            "Managed Switches can use Spanning Tree Protocol (STP), which intelligently figures out the least distance path to a point. STP lets you have network loops and survive. \n\nTry pinging pc1 twice from pc0. The first time, some packets are lost. But the second time the packet goes where it should."
        ),
    },
    "0.3.6": {
        "title": _("Frozen!"),
        "info": _(
            "Every once in a while a piece of hardware will freeze up and needs to be rebooted. \n\nTry pinging laptop1 from pc0 and see how the packet fails. It does not get past the switch. Tap or click the switch and power it off, then power it back on. Now try pinging laptop1."
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
            "Occasionally a piece of hardware will break. This often happens after long periods of use, though sometimes after just sitting around unused. This puzzle makes it look a little worse than it usually would look. \n\nTap or click on the switch and turn it on. After that, select it again and replace it. Things that have been replaced will need to have their settings put back. So make sure to give the new switch a good IP and netmask."
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
            "pc0 cannot ping one of the other computers. Figure out which one, and change the IP address of that computer so it works."
        ),
    },
    "1.2": {
        "title": _("Bad DHCP"),
        "info": _(
            'The server is giving out bad DHCP. Edit the DHCP settings to tell it to give correct DHCP. (You do this by selecting "DHCP" from the device-editing screen.) Then do a DHCP request on all the PCs.'
        ),
    },
    "1.3": {
        "title": _("Gateway Puzzle"),
        "info": _(
            "The items on one network cannot ping the items on the other network (separated by the router). Figure out why and fix it. All computers and switches need fixing, but the router is OK."
        ),
    },
    "1.4": {
        "title": _("Duplicate IPs"),
        "info": _("Get the PCs so they are happy."),
    },
    "1.4.1": {
        "title": _("Two Subnets, Shared Network"),
        "info": _(
            "This network has two different subnets using the same switch. Ping from the different PCs to machines on the other network.\n\nThis is a two-part network; you will see this same network again in the next puzzle, but using one router instead of two. We will use these concepts later on, when we are dealing with security."
        ),
    },
    "1.4.2": {
        "title": _("Two Subnets, Shared Network2"),
        "info": _(
            "This network has two different subnets using the same switch. The router has two interfaces (IP addresses, both on eth0). One network card functions like two. Ping from the different PCs to machines on the other network.\n\nThis is the same network as the previous one, except it uses one router instead of two. We will be using this concept later on when we talk about security. The reason we will use it, is that we may want to have different groups of people on a network (maybe students, faculty, and guests), and we want to have different security levels for each group. By having student traffic need to go through one router before it gets to the staff network, we can set up firewall rules to block students from accessing faculty data. But, that is for a later puzzle."
        ),
    },
    "1.4.3": {
        "title": _("Adding Devices"),
        "info": _(
            "This puzzle has three tasks to it:\n1) Give the switch an IP address.\n2) Add an IP-Phone to the network, linking it to the switch, and then do a DHCP request for it.\n3) Ping the switch from the IP-Phone."
        ),
    },
    "1.5": {
        "title": _("Add DHCP Server"),
        "info": _(
            "These IP-Phones cannot have a static IP. You must add a server on the 192.168.1.0 network and configure the DHCP server. Give an IP to the phone, so the phone can ping the PCs on the other side of the network."
        ),
    },
    "1.6": {
        "title": _("Bad Gateway"),
        "info": _(
            "Computers can only communicate with other computers that are local to them. Gateways must have an IP address that is local to the client. Ping pc0 from pc1 and see if you can spot the error."
        ),
    },
    "1.7": {
        "title": _("Duplicate MAC addresses"),
        "info": _(
            "This puzzle shows you what happens when there are duplicate MAC addresses. This rarely happens, but it used to happen more often than should be statistically probable. Cheap network card vendors used to make batches of cards with the same MAC address, and occasionally someone would buy two of them. The best solution is to replace one of the NICs that has the duplicate MAC address. Ping both pc0 and pc1 from pc2."
        ),
    },
    "1.9.7": {
        "title": _("Bad Netmask"),
        "info": _(
            'One of the subnets has a poorly crafted subnet. There are two ways to represent subnets. The "dot-decimal" notation (255.255.255.0) and CIDR (/24). \n\nHere, we are using a subnet of 255.255.255.129. The 129, in binary, is 10000001. That trailing 1 is the problem. It basically puts the odd numbers in one subnet and the even numbers in the other subnet. While it is possible to get networks to function with a terrible subnet mask like this, do not do it. Use numbers that are properly represented by CIDR notation. Basically, in binary, you want a bunch of 1s, followed by 0s.  (111000), not 1s and 0s intermingled.  (10101). CIDR (/25) represents the number of 1s, and the rest are 0.\n\nTo solve this puzzle, find the IP Addresses that have the /? and change the subnet to something that works. Then, try pinging.'
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
    "2.0": {
        "title": _("Firewall Test"),
        "info": _(
            'This puzzle shows off how a firewall works. You can ping out of a firewall, but not ping the computers behind it. To "solve" this, ping the lone computer from both subnets, and try to ping both subnets from the lone PC.'
        ),
    },
    "2.0.1": {
        "title": _("Firewall Test 2"),
        "info": _(
            "Firewall devices can have an advanced firewall. You can control which interfaces can ping which interfaces. This allows you to protect one side of the LAN from the other. We will use this functionality a lot more later on. \n\nThis technology is mainly used for VLAN security, or setting up a DMZ. To do this puzzle, remove the firewall rule that is keeping the one side from pinging the other side."
        ),
    },
    "2.1": {
        "title": _("VPN Demo"),
        "info": _(
            "Some devices allow you to create VPNs. A Virtual Private Network (VPN) allows you to connect up to things behind a firewall. For this example, you need to ping from pc0 to a number of different things just to see how the VPN works. Make sure you edit one or more of the firewalls to see how the VPN is configured, and see how the static route is defined to make the packets go through the VPN. You will need to know how that works to solve the rest of this level."
        ),
    },
    "2.1.1": {
        "title": _("Bad Encryption"),
        "info": _(
            "The VPNs need their encryption keys fixed. Ping from pc0 to pc1 to ensure it works."
        ),
    },
    "2.1.2": {
        "title": _("Bad VPN IP"),
        "info": _(
            "The VPN Network card has the wrong IP address. Fix the IP address on the firewall VPN, and then ping from pc0 to pc1 through the VPN."
        ),
    },
    "2.1.3": {
        "title": _("Bad Route"),
        "info": _(
            "One of the firewalls is missing a route to tell it to use the VPN. Configure the route and then ping from pc0 to pc1 to make sure it works."
        ),
    },
    "2.5": {
        "title": _("Build a VPN"),
        "info": _(
            "Both firewalls need their VPNs configured. Do not forget to make the right routes!"
        ),
    },
    "2.5.1": {
        "title": _("Blast from the past"),
        "info": _(
            "There are a few problems with this puzzle. pc0 needs to ping pc1, and pc1 needs to ping pc0."
        ),
    },
    "2.6": {
        "title": _("Connect the dots"),
        "info": _(
            "Connect the firewalls to the router, setting up working IPs. Do not forget the VPN!"
        ),
    },
    "2.7": {
        "title": _("Not Working"),
        "info": _(
            'Someone has been trying to set up a VPN between two sites. "It is just not working!" they tell you. I guess it is up to you to figure out what they did wrong. Get pc0 to ping pc1.'
        ),
    },
    "2.7.5": {
        "title": _("Cannot connect"),
        "info": _(
            "The director shut down the office when he went away for the weekend, and brought back this new laptop (laptop2) to connect up. It is not working, and you need to fix your network."
        ),
    },
    "2.9": {
        "title": _("VPN Woes"),
        "info": _(
            "For routing to work, you need to have different IP addresses on the other side of the route. Here we have two networks that are using the same IP address scheme. To get them to work, you will need to change the IP Addresses of one of the networks. It is easiest to change the right network to be 192.168.2.x, as the left network has the right routes already set up for that network."
        ),
    },
    "2.1.5": {
        "title": _("VPNs and traceroute"),
        "info": _(
            'Packets that go through a VPN are "encapsulated."  This means that they are packed up and put inside a VPN packet. A traceroute packet has a "TTL" (Time to Live). Every router along the path is supposed to subtract one from the TTL, and when the TTL is zero, the device that has it will drop the traceroute packet and respond to the originating machine. \n\nAs you do the traceroutes, notice that the router in the center never responds to the traceroute. That is because the traceroute packet is encapsulated. The "outside" packet has a normal TTL, and so the router in the middle never drops the packet. But, the firewall in the middle decrypts the packet, processes it, and sends it on. That firewill will respond to the traceroute.'
        ),
    },
    "3.1": {
        "title": _("Busted"),
        "info": _("Something does not work. Get laptop0 to ping laptop1."),
    },
    "3.2": {
        "title": _("Nowhere to Go"),
        "info": _("Get pc2 to ping pc1, and pc1 to ping pc2."),
    },
    "3.2.5": {
        "title": _("Phoney Network"),
        "info": _("Get phone0 to ping phone2, and also get phone2 to ping phone0."),
    },
    "3.3": {
        "title": _("VPNify"),
        "info": _(
            "Both networks work, but they need to be connected via VPN. You have success when pc2 can ping pc1, and pc3 can ping pc0."
        ),
    },
    "3.4": {
        "title": _("Black Hole"),
        "info": _(
            "There is a black-hole that is eating all the packets. Determine why and fix it."
        ),
    },
    "3.5": {
        "title": _("Middle Man Out"),
        "info": _(
            "The techie setting this one up forgot something. Figure out what he forgot and find some way to fix it."
        ),
    },
    "3.6": {
        "title": _("Two DHCP servers"),
        "info": _(
            "There is a problem with the DHCP on the network. Have all of the devices do a DHCP request. Then have laptop3 ping the various hosts (tap or click laptop3 and see what to ping). See if you can determine what the problem is."
        ),
    },
    "3.6.1": {
        "title": _("It is dead, Jim!"),
        "info": _(
            "This network has a number of small glitches with it. Luckily, they know your phone number. It is nice having a techie around when things go wrong!"
        ),
    },
    "3.7": {
        "title": _("Grand Central Station"),
        "info": _(
            "The router in the middle was replaced. While you are at it, they want you to create a VPN to connect all three networks. Hope they are paying you well!"
        ),
    },
    "3.8": {
        "title": _("Encryption Troubles"),
        "info": _(
            "Your friends have another problem. There was an issue with the encryption on their VPN. They tried to fix it, but it is still failing."
        ),
    },
    "3.12": {
        "title": _("What you cannot see can hurt you"),
        "info": _(
            "They say they did not do anything, but suddenly everything stopped working. Now that you are back from your trip, can you fix it?"
        ),
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
