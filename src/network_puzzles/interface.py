class interface:
    nicname=str
    ip=str
    vlan=[]

    def __init__(self, interfacerec=None):
        if interfacerec == None:
            interfacerec = {}
        self.nicname = interfacerec['nicname']
        self.ip = interfacerec['myip']
        self.vlan = []
        if 'VLAN' in interfacerec:
            if not isinstance(interfacerec['VLAN'],list):
                interfacerec['VLAN'] = [interfacerec['VLAN']]
            for onevlan in interfacerec['VLAN']:
                self.vlan.append(onevlan) #we do not need to do a deep copy or anything
