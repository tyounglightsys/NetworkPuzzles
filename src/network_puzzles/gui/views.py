import logging

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


class FirewallRulesRecView(AppRecView):
    # NOTE: self.root is defined in popups.kv, which makes it not yet available
    # during __init__.
    def on_selection(self, index):
        self.root.on_rule_selection(self.data[index])

    def update_data(self):
        self.data = []
        logging.debug(f"Views: {len(self.root.device.firewall_rules)=}")
        for rule in self.root.device.firewall_rules:
            text = f"  {rule.get('source')} - {rule.get('destination')} -> {rule.get('action')}"
            self.data.append({"text": text, "data": rule})


class IPsRecView(AppRecView):
    def on_selection(self, index):
        self.root.on_ip_selection(self.data[index].get("text"))

    def update_data(self, ips):
        self.data = [{"text": f"{d.get('ip')}/{d.get('mask')}", "data": d} for d in ips]


class NICsRecView(AppRecView):
    def on_selection(self, index):
        self.root.on_nic_selection(self.data[index])

    def update_data(self, nics, management=True):
        data = []
        for n in nics:
            if n.name.startswith("lo"):
                continue
            text = n.name
            # Add "*" to text if iface is connected.
            if n.is_connected():
                text += "*"
            # Add MAC address to NIC description.
            text += f"; {n.mac}"
            data.append({"text": text, "data": n})
        item = {"text": "management_interface0"}
        if not management and item in data:
            data.remove(item)
        self.data = data


class PuzzlesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.update_puzzle_list()
        self.update_data()

    def update_data(self):
        self.data = [{"text": n} for n in self.app.filtered_puzzlelist]


class RoutesRecView(AppRecView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_selection(self, index):
        self.root.on_route_selection(self.data[index], inst=self)

    def update_data(self, static=False):
        def t(data):
            ip = data.get("ip")
            mask = data.get("mask")
            gw = data.get("gateway")
            return f"IP:{ip:<20.20} Mask:{mask:<20.20} GW:{gw:<20.20}"

        if static:
            routes = self.root.device.routes
        else:
            routes = self.root.device.get_routes_from_nics()
        self.data = [{"text": t(r), "data": r} for r in routes]
