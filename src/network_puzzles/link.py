import copy

class link:
    def __init__(self, linkrec):
        self.hostname = linkrec['hostname']
        self.linktype = linkrec['linktype']
        self.uniqueidentifier = linkrec['uniqueidentifier']
        self.SrcNic = copy.copy(linkrec['SrcNic'])
        self.DstNic = copy.copy(linkrec['DstNic'])