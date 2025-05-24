import time

from . import puzzle
from . import session
from . import link
from . import nic

def getPacketLocation(packetrec):
    """
    Return the x/y location of a paket.
    Args: packetrec - a valid packet structure.
    returns: an {x,y} structure showing the center-point of the packet or None
    """
    if(packetrec is None or 'packetlocation' not in packetrec):
        return None
    #packets are only displayed when they are on links.
    thelink = puzzle.linkFromName(packetrec['packetlocation'])
    if (thelink is None):
        return None #We could not find the link
    #if we get here, we have the link that the packet is on
    sdevice = puzzle.deviceFromID(thelink['SrcNic']['hostid'])
    ddevice = puzzle.deviceFromID(thelink['DstNic']['hostid'])
    if(sdevice is None or ddevice is None):
        return None #This should never happen.  But exit gracefully.
    if packetrec['packetDirection'] == 1:
        #set the start of the link as the source
        sx, sy = splitXYfromString(sdevice['location'])
        dx, dy = splitXYfromString(ddevice['location'])
    else:
        #set the start of the link as the destination
        sx, sy = splitXYfromString(ddevice['location'])
        dx, dy = splitXYfromString(sdevice['location'])
    #We now have a line that the packet is somewhere on.
    deltax = (sx - dx) / 100
    deltay = (sy - dy) / 100

    amountx = deltax * packetrec['packetDistance']
    amounty = deltay * packetrec['packetDistance']

    #return a {x,y} structure
    return { sx + amountx , sy + amounty }

def newPacket():
    """Returns an empty packet with all the fields."""
    nPacket={
        'packetype':"",
        'VLANID':0, #start on the default vlan
        'health':100, #health.  This will drop as the packet goes too close to things causing interferance
        'sourceIP':"",
        'destIP':"",
        'sourceMAC':"",
        'destMAC':"",
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
        return { ix, iy}
    except ValueError:
        return None

def addPacketToPacketlist(thepacket):
    if thepacket is not None:
        session.packetlist.append(thepacket)

def packetsNeedProcessing():
    """determine if we should continue to loop through packets
    returns true or false"""
    return len(session.packetlist) > 0

def processPackets(killSeconds:int=20):
    """
    Loop through all packets, moving them along through the system
    Args: killseconds - the number of seconds to go before killing the packets.
    """
    killMilliseconds = killSeconds * 1000
    #here we loop through all packets and process them
    curtime = int(time.time() * 1000)
    for one in session.packetlist:
        #figure out where the packet is
        theLink = puzzle.linkFromName(one['packetlocation'])
        if theLink is not None:
            #the packet is traversing a link
            one['packetDistance'] += 10 #traverse the link.  If we were smarter, we could do it in different chunks based on the time it takes to redraw
            if one['packetDistance'] > 100:
                #We have arrived.  We need to process the arrival!
                #get interface from link
                nicrec = theLink['SrcNic']
                if one['packetDirection'] == 2:
                    nicrec = theLink['DstNic']
                tNic = link.getInterfaceFromLinkNicRec(nicrec)
                if tNic is None:
                    #We could not find the record.  This should never happen.  For now, blow up
                    print ("Bad Link:")
                    print (theLink)
                    print ("Direction = " + str(one['packetDirection']))
                    raise Exception("Could not find the endpoint of the link. ")
                #We are here.  Call a function on the nic to start the packet entering the device
                nic.beginIngress(one, tNic)

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
    