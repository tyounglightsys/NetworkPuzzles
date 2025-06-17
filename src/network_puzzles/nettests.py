from . import messages


class NetTest:
    def __init__(self, data):
        self.json = data

    @property
    def dhost(self):
        return self.json.get('dhost')

    @property
    def shost(self):
        return self.json.get('shost')

    @property
    def name(self):
        return self.json.get('thetest')

    def get_help_text(self, help_level):
        key = self._get_help_level_key(help_level)
        helps = messages.nettests.get(self.name)
        if helps:
            text = helps.get(key)
            if text.endswith(':'):
                text += f" {self._get_help_extra_text()}"
        else:
            text = ''
        return text
    
    def _get_help_extra_text(self):
        # TODO: Verify that the extra text is always nettest's "dhost".
        return self.dhost

    def _get_help_level_key(self, help_level):
        match help_level:
            case 1:
                key = "basic"
            case 2:
                key = "hints"
            case 3:
                key = "full"
            case 0|_:
                key = None
        return key