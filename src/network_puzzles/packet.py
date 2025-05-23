from . import puzzle

def getPacketLocation(packetrec):
    """
    Return the x/y location of a paket.
    Args: packetrec - a valid packet structure.
    returns: an {x,y} structure showing the center-point of the packet or None
    """
    if(packetrec == None or not 'packetlocation' in packetrec):
        return None
    #packets are only displayed when they are on links.
    thelink = puzzle.linkFromName(packetrec['packetlocation'])
    if (thelink == None):
        return None #We could not find the link
    #if we get here, we have the link that the packet is on
    sdevice = puzzle.deviceFromID(thelink['SrcNic']['hostid'])
    ddevice = puzzle.deviceFromID(thelink['DstNic']['hostid'])
    if(sdevice == None or ddevice == None):
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
        'payload':"",
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

