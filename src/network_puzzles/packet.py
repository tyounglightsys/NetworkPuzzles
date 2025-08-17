import time
import ipaddress
import re
import logging

from . import session
from . import device

def getPacketLocation(packetrec):
    """
    Return the x/y location of a paket.
    Args: packetrec - a valid packet structure.
    returns: an {x,y} structure showing the center-point of the packet or None
    """
    if(packetrec is None or 'packetlocation' not in packetrec):
        return None
    #packets are only displayed when they are on links.
    thelink = session.puzzle.link_from_name(packetrec['packetlocation'])
    if (thelink is None):
        return None #We could not find the link
    #if we get here, we have the link that the packet is on
    sdevice = session.puzzle.device_from_uid(thelink['SrcNic']['hostid'])
    ddevice = session.puzzle.device_from_uid(thelink['DstNic']['hostid'])
    if(sdevice is None or ddevice is None):
        return None #This should never happen.  But exit gracefully.
    if packetrec['packetDirection'] != 1:
        #swap the source and destination
        tdevice = sdevice #stash it temporarily
        sdevice = ddevice
        ddevice = tdevice
    #Now the source and destination are appropriately set
    sx, sy = splitXYfromString(sdevice['location'])
    dx, dy = splitXYfromString(ddevice['location'])    
    #We now have a line that the packet is somewhere on.
    deltax = (dx - sx) / 100
    deltay = (dy - sy) / 100

    amountx = deltax * packetrec['packetDistance']
    amounty = deltay * packetrec['packetDistance']

    tx = sx + amountx
    ty = sy + amounty

    #return a [x,y] structure
    return [ tx , ty ]

def newPacket():
    """Returns an empty packet with all the fields."""
    nPacket={
        'packettype':"",
        'VLANID':0, #start on the default vlan
        'health':100, #health.  This will drop as the packet goes too close to things causing interferance
        'sourceIP':"",
        'sourceMAC':"",
        'destIP':"",
        'destMAC':"",
        'tdestIP':"",#If we are going through a router.  Mainly so we know which interface we are supposed to be using
        'status':"good",
        'statusmessage':"",
        'payload':"",
        'starttime': int(time.time() * 1000), #secondssince epoc.  Failsafe that will kill the packet if too much time has passed
        'packetlocation':"",#where the packet is.  Should almost always be a link name
        'packetDirection':0, #Which direction are we going on a network link.  1=src to dest, 2=dest to src
        'packetDistance':0 #The % distance the packet has traversed.  This is incremented until it reaches 100%
    }
    return nPacket

def splitXYfromString(xystring:str):
    """Take a string like "50,50" and change it to be { 50,50 }
    Args: xystring:str - a string with an x and y value, separated by a comma
    Returns: an {x,y} struct, which can be assigned by x,y = splitXYfromString("50,50")
    Note: if it is broken, it will return None, which the break the above line.
    """
    try:
        sx, sy =xystring.split(',')
        ix = int(sx)
        iy = int(sy)
        return [ ix, iy]
    except ValueError:
        return None

def distance(sx,sy,dx,dy):
    #we have a 5/5 grid that we are working with.
    #The ** is the exponent.  **2 is squared, **.5 is the square-root
    return ((((sx - dx) **2) + ((sy - dy) **2 )) **.5) / 5

def damagePacketIfNeeded(packetrec, packetnumber, pointlist):
    """
    Search damage the packet if wireless+microwave or wired+light
    """
    #packets are only displayed when they are on links.
    thelink = session.puzzle.link_from_name(packetrec['packetlocation'])
    if (thelink is None):
        return None #We could not find the link
    #if we get here, we have the link that the packet is on
    for one in session.puzzle.devices:
        doit = False
        if one.get('mytype') == "microwave" and thelink.get('linktype') == "wireless":
            doit=True
        if one.get('mytype') == "fluorescent" and thelink.get('linktype') != "wireless":
            doit=True
        if doit:
            #We need to check for damage.
            dx, dy = splitXYfromString(one.get('location'))
            #calculate the centerpoint
            halfsize = 50 #all devices in EduNetworkBuilder were 100 size
            dx = dx + halfsize
            dy = dy + halfsize

            #now compare locations to each point along the distance.
            for onepoint in pointlist:
                px, py = onepoint
                #calculate distance
                dist = int(distance(px,py,dx,dy))
                if dist < 34:
                    session.print(f"Checking damage {packetnumber}: {packetrec['packettype']} {packetrec['health']} - {px},{py} {dx},{dy} distance: {dist} {packetrec['packetlocation']}")
                if dist <= 32:
                    packetrec['health'] = packetrec['health'] - 10
                    session.print(f"Packet damaged {packetnumber}: {packetrec['packettype']} {packetrec['health']} - distance: {dist}")
                    if packetrec['health'] <= 0:
                        packetrec['status'] = 'done' #the packet dies silently

def addPacketToPacketlist(thepacket):
    if thepacket is not None:
        session.packetlist.append(thepacket)

def packetsNeedProcessing():
    """determine if we should continue to loop through packets
    returns true or false"""
    if len(session.packetlist) > session.maxpackets:
        session.maxpackets = len(session.packetlist)
    if len(session.packetlist) > 30:
        if not session.packetstorm:
            logging.info(f"We started a storm: {len(session.packetlist)}")
        session.packetstorm = True #There were too many packets.  Must have created a storm/net loop
    return len(session.packetlist) > 0

def packetDistancePoints(packetrec, tick_pct):
    if(packetrec is None or 'packetlocation' not in packetrec):
        return None
    #packets are only displayed when they are on links.
    thelink = session.puzzle.link_from_name(packetrec['packetlocation'])
    if (thelink is None):
        return None #We could not find the link
    #if we get here, we have the link that the packet is on
    sdevice = session.puzzle.device_from_uid(thelink['SrcNic']['hostid'])
    ddevice = session.puzzle.device_from_uid(thelink['DstNic']['hostid'])
    if(sdevice is None or ddevice is None):
        return None #This should never happen.  But exit gracefully.
    if packetrec['packetDirection'] != 1:
        #swap the source and destination
        tdevice = sdevice #stash it temporarily
        sdevice = ddevice
        ddevice = tdevice
    #Now the source and destination are appropriately set
    sx, sy = splitXYfromString(sdevice['location'])
    dx, dy = splitXYfromString(ddevice['location'])
    #We now have a line that the packet is somewhere on.
    deltax = (dx - sx) / 100
    deltay = (dy - sy) / 100

    myarray = list()

    for a in range(int(packetrec['packetDistance']), int(packetrec['packetDistance'] + tick_pct),2):
        tx = sx + (deltax * a)
        ty = sy + (deltay * a)
        myarray.append([tx,ty])

    return myarray    

def processPackets(killSeconds: int = 20, tick_pct: float = 10):
    """
    Loop through all packets, moving them along through the system
    Args: killseconds - the number of seconds to go before killing the packets.
    """
    killMilliseconds = killSeconds * 1000
    #here we loop through all packets and process them
    curtime = int(time.time() * 1000)
    counter=0
    for one in session.packetlist:
        counter = counter + 1
        # figure out where the packet is
        theLink = session.puzzle.link_from_name(one['packetlocation'])
        if theLink is not None:
            #the packet is traversing a link
            pointlist = packetDistancePoints(one, tick_pct)
            one['packetDistance'] += tick_pct
            damagePacketIfNeeded(one, counter, pointlist)
            if one['packetDistance'] > 50 and theLink.get('linktype') == 'broken':
                #The link is broken.  The packet gets killed
                one['status'] = 'done' #the packet dies silently
            if one['packetDistance'] > 100 and one['status'] != 'done':
                #We have arrived.  We need to process the arrival!
                #get interface from link
                nicrec = theLink['SrcNic']
                if one['packetDirection'] == 1:
                    nicrec = theLink['DstNic']
                tNic = device.getDeviceNicFromLinkNicRec(nicrec)
                if tNic is None:
                    #We could not find the record.  This should never happen.  For now, blow up
                    print ("Bad Link:")
                    print (theLink)
                    print ("Direction = " + str(one['packetDirection']))
                    raise Exception("Could not find the endpoint of the link. ")
                #We are here.  Call a function on the nic to start the packet entering the device
                #print ("packet finished " + one['packetlocation'] + " and is moving onto " + tNic['myid']['hostname'])
                device.doInputFromLink(one, tNic)

        #If the packet has been going too long.  Kill it.
        if curtime - one['starttime'] > killMilliseconds:
            #over 20 seconds have passed.  Kill the packet
            one['status'] = 'failed'
            one['statusmessage'] = "Packet timed out"
    #When we are done with all the processing, kill any packets that need killing.
    cleanupPackets()

def cleanupPackets():
    """After processing packets, remove any "done" ones from the list."""
    for index in range(len(session.packetlist) - 1, -1, -1): 
        one = session.packetlist[index]
        match one['status']:
            case 'good':
                continue
            case 'failed':
                #We may need to log/track this.  But we simply remove it for now
                del session.packetlist[index]
                continue
            case 'done':
                #We may need to log/track this.  But we simply remove it for now
                del session.packetlist[index]
                continue
            case 'dropped':
                #packets are dropped when they are politely ignored by a device.  No need to log
                del session.packetlist[index]
                continue
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
    if not isinstance(ip,str):
        ip = str(ip) #change it to a string
    ip = re.sub("/.*","", ip)
    return ip 

def isLocal(packetIP:str, interfaceIP:str):
    """Determine if the packet IP is considered local by the subnet/netmask on the interface IP
    Args:
        packetIP:str - a string IP (ipv6/ipv4); just an IP - no subnet
        interfaceIP:str - an IP/subnet, either iPv4 or ipv6"""
    t_packetIP = justIP(packetIP)
    try:
        ip = ipaddress.ip_address(t_packetIP)
        network = ipaddress.ip_network(interfaceIP, strict=False) #The interface will have host bits set, so we choose false
        return ip in network
    except ValueError:
        # Handle invalid IP address or subnet format
        return False

def BroadcastMAC():
    """"return the broadcast MAC address: FFFFFFFFFFFF"""
    return "FFFFFFFFFFFF"

def isBroadcastMAC(macToCheck:str):
    """Check to see if the mac address is the broadcast one.  Should be FFFFFFFFFFFF"""
    if macToCheck == "FFFFFFFFFFFF":
        return True
    if macToCheck == "FF:FF:FF:FF:FF:FF":
        return True
    if macToCheck == "FF-FF-FF-FF-FF-FF":
        return True
    return False
    
def isEmpty(iptocheck:str):
    if iptocheck == "0.0.0.0":
        return True