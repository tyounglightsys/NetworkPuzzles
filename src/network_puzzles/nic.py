import random


class Nic:
    def __init__(self, nicrec):
        if not isinstance(nicrec, dict):
            raise ValueError(f"Invalid JSON data passed to {self.__class__}.")
        self.json = nicrec
        #add the interfaces
        if not isinstance(nicrec.get('interface'), list):
            nicrec['interface'] = [nicrec['interface']] #make it a list so we can itterate it

    def ensure_mac(self, data=None):
        if data is not None:
            new_data = data
        else:
            new_data = self.json

        if 'Mac' not in new_data:
            #Most of the network cards do not have this done yet.  We generate a new random one
            localmac=""
            for i in range(1,13):
                localmac = localmac + random.choice("ABCDEF1234567890")
            new_data['Mac'] = localmac

        self.json = new_data
        return new_data