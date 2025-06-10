from . import _

puzzles = {
    "0.0": {
        'title': _("Learn how help works"),
        'message': _("To learn how this program works, first we will acquaint you with the 'Help.'  Most of the puzzles you do, you will want to do with as little help as possible.  But, there is help when you need it.  For this puzzle, click one of the four help-levels (round buttons) on the right.  Then mouse-over the PC and see the messages.  When you have moused-over for all the buttons (and pressed the ? box), this puzzle will be completed.")
    },
    "0.1": {
        "title": _("Ping Test"),
        "message": _("Right-click PC0 and ping laptop0 and laptop1.  You can put either the IP address or host-name of the device you are trying to ping in the box that pops up asking you for an IP."),
    },
    "0.1.1": {
        'title': _("Plug in network"),
        'message': _("Plug in the network to the computer that needs it.  Click on the link icon (the line) and drag the pointer from the switch to the computer.  When you release the mouse button, the link window will pop up.  Choose the ports you want to connect, and you should be finished."),
    },
    "0.2": {
        'title': _("No Switch"),
        'message': _("There is no switch.  Add one and link the devices to it.  Click on the switch and add it to the network (make sure you add a switch and not a hub).  Then, drag links from the switch to the computers, choosing the ports to connect."),
    },
    "0.2.5": {
        "title": _("Power It On"),
        "message": _("The switch is powered off.  Right-click it and power it on.  Then, ping the laptop to make sure things work."),
    },
    "0.3": {
        "title": _("DHCP Request"),
        "message": _("Tell the PC to do a DHCP request.  Right-click on the PC to see the menu, or do it from the 'All' menu."),
    },
    "0.3.1": {
        'title': _("IP Puzzle"),
        'message': _("pc0 needs an IP that is local to the other two computers.  Double-click PC0, double-click the IP-Address (0.0.0.0) and put a good IP address there."),
    },
    "0.3.4": {
        'title': _("Network Loop"),
        'message': _("This puzzle shows you what happens when you create a network loop.  A loop is made when you have your switches connected to themselves or to another one that is connected back to the first one.  Ping from pc0 to pc1 to see what happens.  You do not need to fix the problem, but right-clicking one of the switches and removing one of the offending links would do it."),
    },
    "0.3.5": {
        'title': _("Network Loop 2"),
        'message': _("Managed Switches can use Spanning Tree, which intelligently figures out the least distance path to a point.  It is made so you can have network loops and survive.  Try pinging pc1 twice from pc0.  The first time, some packets are lost.  But the second time the packet goes where it should."),
    },
    "0.3.6": {
        'title': _("Frozen!"),
        'message': _("Every once in a while a piece of hardware will freeze up and needs to be rebooted.  \n\nTry pinging laptop1 from PC0 and see how the packet fails.  It does not get past the switch.\n\nRight-click the switch and power it off, then power it back on.  Now try pinging laptop1."),
    },
    "0.4": {
        'title': _("Switch vs Hub"),
        'message': _("This puzzle shows the difference between a hub and a switch.\nHave each of the servers ping the computers on the same lan as themselves, and have those computers ping the server.  \nThe switch learns which device is attached to it and only sends the packet to that computer, while the hub sends the packet to every device on the subnet."),
    },
    "0.5": {
        'title': _("Where did I put that?"),
        'message': _("Your boss bought a switch and plugged it into your network, but did not tell you where he put it.  Now he wants you to find it.\nWhat do you do when you know where something is, but not exactly?  You go to the device you know it is plugged into and follow the wire.\nTo solve this, drag the switch around, and then find the other end of the wire and \"drag\" on the empty spot to \"find\" it.  Then, change the IP address of the missing switch."),
    },
    "0.6": {
        'title': _("Broken Link"),
        'message': _("This shows what happens if there is a broken network wire in your network.  Ping laptop1 and see where the packet dies.  Open one of the devices connected to that link and you will see that, even though the device has a link connected to it, it does not have a \"connection light\" saying it is connected.  (The connection-light is the * at the end of the eth name).  You can also edit the network card to see if it thinks it is connected.  Remove the broken network wire by right-clicking one of the devices at either end and removing the link.  Then add the link again.  A successful ping tells you if you got it working."),
    },
    "0.6.5": {
        'title': _("Packet Corruption"),
        'message': _("Network wires that run too close to electrical wires or fluorescent lights can cause packet corruption.  Move the light out of the way if the packet get corrupted."),
    },
    "0.6.6": {
        'title': _("Packet Corruption2"),
        'message': _("Packets can be partially corrupted by lights.  Look at how the packet goes the first time.  Move the light out of the way just a little bit and it should work fine.")
    },
    "0.7": {
        "title": _("Traceroute"),
        "message": _("A traceroute tests the path from one computer to the other.  Every routing device along the path will respond (but switches do not).  \nThis is done by adding a TTL (Time to Live) number on every packet.  Each device that routes packets will subtract one from the TTL.  When the TTL reaches zero, the devices will send a response back.  Traceroute catches these responses and uses it to determine what each step is along the path.\nHave server0 traceroute to server1"),
    },
    "0.10.1": {
        'title': _("Bad Power Supply"),
        'message': _("Occasionally a piece of hardware will break, This often happens after long periods of use, though sometimes after just sitting around unused.\n\nThis puzzle makes it look a little worse than it usually would look.  Go ahead and turn on the switch.  After that, right-click and replace it.\n\nThings that have been replaced will need to have their settings put back.  So make sure to give the new switch a good IP and gateway."),
    },
    "0.10.2": {
        'title': _("Bad Power - Needs UPS"),
        'message': _("Occasionally the electricity in a building, or in a city, has problems.  Usually, in these cases, a device will function for a while and then break on you.  To make the puzzle go faster, however, we have it break immediately.\n\nThis puzzle makes it look a little worse than it usually would look.  Go ahead and turn on the switch.  After that, right-click and replace it.  If you turn it on again, it will continue to break until you add a UPS to it.  After that, it will be fine.  Luckily for you, you do not need to pay for the devices you keep replacing!\n\nThings that have been replaced will need to have their settings put back.  So make sure to give the new switch a good IP and gateway."),
    },
    "1.1": {
        "title": _("Bad IP"),
        "message": _("PC0 cannot ping one of the other computers.  Figure out which one, and change the IP address of that computer so it works."),
    },
    "1.2": {
        "title": _("Bad DHCP"),
        "message": _("The Server is giving out bad DHCP.  Edit the DHCP settings to tell it to give correct DHCP.  (You do this by selecting 'DHCP' from the device-editing screen) Then do a DHCP request on all the PCs."),
    },
    "1.3": {
        "title": _("Gateway Puzzle"),
        "message": _("The items on one network cannot ping the items on the other network (separated by the router).  Figure why and fix it.  All computers and switches need fixing, but the router is OK."),
    },
    "1.4": {
        "title": _("Duplicate IPs"),
        "message": _("Get the PCs so they are happy"),
    },
    "1.4.1": {
        "title": _("Two Subnets, Shared Network"),
        "message": _("This network has two different subnets using the same switch.  Ping from the different PCs to machines on the other network.\nThis is a two-part network; you will see this same network again in the next puzzle, but using one router instead of two.  We will use these concepts later on, when we are dealing with security."),
    },
    "1.4.2": {
        "title": _("Two Subnets, Shared Network2"),
        "message": _("This network has two different subnets using the same switch.  The router has two interfaces (IP addresses, both on eth0). One network card functions like two.  Ping from the different PCs to machines on the other network.\nThis is the same network as the previous one, except it uses one router instead of two.  We will be using this concept later on when we talk about security.  The reason we will use it, is that we may want to have different groups of people on a network (maybe students, faculty, and guests), and we want to have different security levels for each group.  By having student traffic need to go through one router before it gets to the staff network, we can set up firewall rules to block students from accessing faculty data.  But, that is for a later puzzle."),
    },
    "1.4.3": {
        "title": _("Adding Devices"),
        "message": _("This puzzle has three tasks to it:\n1) Give the switch an IP address\n2) Add an IP-Phone to the network, linking it to the switch, and then do a DHCP request for it.\n3) Ping the switch from the IP-Phone"),
    },
    "1.5": {
        "title": _("Add DHCP Server"),
        "message": _("These IP-Phones cannot have a static IP.  You must add a server on the 192.168.1.0 network and configure the DHCP server.  Give an IP to the phone, so the phone can ping the PCs on the other side of the network"),
    },
    "1.6": {
        "title": _("Bad Gateway"),
        "message": _("Computers can only communicate with other computers that are local to them.  Gateways must have an IP address that is local to the client.  Ping pc0 from pc1 and see if you can spot the error."),
    },
    "1.7": {
        "title": _("Duplicate MAC addresses"),
        "message": _("This puzzle shows you what happens when there are duplicate MAC addresses.  This rarely happens, but it used to happen more often than should be statistically probable.  Cheap network card vendors used to make batches of cards with the same MAC address, and occasionally someone would  buy two of them.  The best solution is to replace one of the NICs that has the duplicate MAC address.  Ping both pc0 and pc1 from pc2."),
    },
    "1.9.7": {
        "title": _("Bad Netmask"),
        "message": _("One of the subnets has a poorly crafted subnet.  There are two ways to represent subnets.  The \"dot-decimal\" notation (255.255.255.0) and CIDR (/24). \n\nHere, we are using a subnet of 255.255.255.129.  The 129, in binary, is 10000001.  That trailing 1 is the problem.  It basically puts the odd numbers in one subnet and the even numbers in the other subnet.  While it is possible to get networks to function with a terrible subnet mask like this, do not do it.  Use numbers that are properly represented by CIDR notation.  Basically, in binary, you want a bunch of 1s, followed by 0s.  (111000), not 1s and 0s intermingled.  (10101).  CIDR (/25) represents the number of 1s, and the rest are 0.\n\nTo solve this puzzle, find the IP Addresses that have the /? and change the subnet to something that works.  Then, try pinging."),
    },
    "1.21": {
        "title": _("Practice1"),
        "message": "",
    },
    "1.22": {
        "title": _("Practice2"),
        "message": "",
    },
    "1.23": {
        "title": _("Practice3"),
        "message": "",
    },
    "1.24": {
        "title": _("Practice4"),
        "message": "",
    },
    "1.25": {
        "title": _("Practice5"),
        "message": "",
    },
    "1.26": {
        "title": _("Practice6"),
        "message": "",
    },
    "1.27": {
        "title": _("Practice7"),
        "message": "",
    },
}
