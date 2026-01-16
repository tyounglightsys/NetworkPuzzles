import logging

from kivy.uix.widget import Widget

from ..packet import Packet


class GuiPacket(Widget):
    def __init__(self, base_packet=None, **kwargs):
        if isinstance(base_packet, Packet):
            self.base = base_packet
        elif base_packet is None:
            self.base = Packet()
        else:
            raise ValueError(f"Argument is not a `Packet` type: {type(base_packet)}")
        super().__init__(**kwargs)


class PacketManager:
    """Responsible for drawing and updating ping packets."""

    def __init__(self, app):
        self.app = app

    @property
    def gui_packets(self):
        return self.app.packets

    @property
    def packet_ids(self):
        """Yield a hash of the JSON of each currently active packet."""
        for p in self.app.ui.packetlist:
            yield p.hash_id

    def get_gui_packet(self, pkt):
        """Return GuiPacket whose hash_id matches that of the given Packet."""
        hash_id = pkt.hash_id
        for p in self.gui_packets:
            if hash_id == p.base.hash_id:
                return p

    def get_link_widget(self, link_name):
        link_data = self.app.ui.get_link(link_name)
        return self.app.get_widget_by_hostname(link_data.get("hostname"))

    def update_packets(self, *args):
        """Updates drawn packet widgets in the puzzle, either by adding new ones,
        changing their locations, or by removing them.
        """

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
            hashes = [h for h in self.packet_ids]
            if p.base.hash_id not in hashes:
                self.app.root.ids.layout.remove_widget(p)

        # Add or update packets in layout.
        for p in self.app.ui.packetlist:
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
