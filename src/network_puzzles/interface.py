class Interface:
    nicname: str
    ip: str
    vlan: list

    def __init__(self, interfacerec=None):
        if interfacerec is None:
            interfacerec = {}
        self.nicname: str = interfacerec.get('nicname')
        self.ip: str = interfacerec.get('myip')
        self.vlan: list = []
        if 'VLAN' in interfacerec:
            if not isinstance(interfacerec.get('VLAN'), list):
                interfacerec['VLAN'] = [interfacerec.get('VLAN')]
            for onevlan in interfacerec.get('VLAN'):
                self.vlan.append(onevlan) #we do not need to do a deep copy or anything
