import logging

from kivy.uix.widget import Widget

from ..packet import Packet


class GuiPacket(Widget):
    COLORS = {
        "dhcp": (237 / 255, 51 / 255, 59 / 255),  # red:#ED333B
        "none": (0.5, 0.5, 0.5),  # gray
        "ping": (98 / 255, 160 / 255, 234 / 255),  # blue:#62A0EA
        "traceroute": (192 / 255, 191 / 255, 188 / 255),  # white:#C0BFBC
        "tunnel": (246 / 255, 211 / 255, 45 / 255),  # yellow:#F8E45C -> #F6D32D
    }

    def __init__(self, base_packet=None, **kwargs):
        if isinstance(base_packet, Packet):
            self.base = base_packet
        elif base_packet is None:
            self.base = Packet()
        else:
            raise ValueError(f"Argument is not a `Packet` type: {type(base_packet)}")
        super().__init__(**kwargs)

    @property
    def color(self):
        base_type = self.base.packettype.split("-")[0]
        if base_type not in self.COLORS:
            base_type = "none"
        return self.COLORS.get(base_type)


class PacketManager:
    """Responsible for drawing and updating ping packets."""

    def __init__(self, app):
        self.app = app

    @property
    def gui_packets(self):
        """Return list of existing packet widgets."""
        return self.app.packets

    @property
    def packet_ids(self):
        """Yield a hash of the JSON of each currently active packet."""
        for p in self.app.ui.puzzle.packets:
            yield p.hash_id

    def get_gui_packet(self, pkt):
        """Return GuiPacket whose hash_id matches that of the given Packet."""
        hash_id = pkt.hash_id
        for p in self.gui_packets:
            if hash_id == p.base.hash_id:
                return p

    def get_link_widget(self, link_name):
        link_data = self.app.ui.get_link(link_name)
        if link_data is None:
            # This would cause stuff the next line to explode
            return None
        return self.app.get_widget_by_hostname(link_data.get("hostname"))

    def update_packets(self, *args):
        """Updates drawn packet widgets in the puzzle, either by adding new ones,
        changing their locations, or by removing them.
        """

        # Exit quickly if there are no packets to add or update.
        if not self.app.ui.puzzle.packets and not self.gui_packets:
            return

        # Packet draw index needs to be above link lines but below devices,
        # which means it needs to be one less than the lowest link index, which
        # can change during the course of solving the puzzle if links are added
        # or removed.
        link_idx = self.app.get_first_link_index()
        if link_idx is None:
            # No links loaded; therefore, no packets can be added or removed.
            return
        pkt_idx = link_idx - 1

        # Remove expired packets.
        for p in self.gui_packets:
            if p.base.hash_id not in [h for h in self.packet_ids]:
                self.app.root.ids.layout.remove_widget(p)

        # Add or update packets in layout.
        for p in self.app.ui.puzzle.packets:
            link = self.get_link_widget(p.packet_location)
            # NOTE: Sometimes the layout doesn't contain the link widgets, maybe
            # due to a race condition with a redraw? So skipping packet update
            # if the link isn't found seems to work for now.
            if not link:
                logging.warning(f"Packets: link not found: {p.packet_location}")
                continue

            # Search for existing packet in layout.
            pkt = self.get_gui_packet(p)
            if pkt:
                # Remove from layout before updating positiona and index.
                # NOTE: Removing and re-adding allows the draw index to be
                # updated so that the packet sits on top of the link.
                self.app.root.ids.layout.remove_widget(pkt)
            else:
                # Create new packet.
                pkt = GuiPacket(p)

            # Calculate packet position.
            progress = p.distance
            if p.direction == 2:
                progress = 100 - progress
            center_x, center_y = link.get_progress_pos(progress)

            # Add packet to layout at correct position.
            pkt.pos = (
                center_x - self.app.PACKET_DIMS[0] / 2,
                center_y - self.app.PACKET_DIMS[1] / 2,
            )
            self.app.root.ids.layout.add_widget(pkt, pkt_idx)
