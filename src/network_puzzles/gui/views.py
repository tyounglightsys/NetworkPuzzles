from kivy.uix.recycleview import RecycleView

from .. import session


class AppRecView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = list()
        self.selected_item = None

    @property
    def app(self):
        return session.app

    def on_selection(self, idx):
        self.selected_item = self.data[idx]


class IPsRecView(AppRecView):
    def update_data(self, ips):
        self.data = [{"text": f"{d.get('ip')}/{d.get('mask')}"} for d in ips]

    def on_selection(self, index):
        self.root.on_ip_selection(self.data[index].get("text"))


class NICsRecView(AppRecView):
    def update_data(self, nics, management=True):
        data = []
        for n in nics:
            if n.name.startswith("lo"):
                continue
            text = n.name
            # Add "*" to text if iface is connected.
            if self.app.ui.puzzle.nic_is_connected(n.json):
                text += "*"
            # Add MAC address to NIC description.
            text += f"; {n.mac}"
            data.append({"text": text})
        item = {"text": "management_interface0"}
        if not management and item in data:
            data.remove(item)
        self.data = data

    def on_selection(self, index):
        self.root.on_nic_selection(self.data[index].get("text"))


class PuzzlesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.update_puzzle_list()
        self.selected_item = None
        self.update_data()

    def update_data(self):
        self.data = [{"text": n} for n in self.app.filtered_puzzlelist]
