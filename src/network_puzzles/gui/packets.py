import logging

from kivy.properties import NumericProperty
from kivy.uix.widget import Widget


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
            yield self.get_hash_id(p)

    def get_gui_packet(self, data):
        hash_id = self.get_hash_id(data)
        for p in self.gui_packets:
            if hash_id == p.hash_id:
                return p

    def get_hash_id(self, data):
        """Get unique identifier by hashing specific properties of packet data."""
        src_ip = data.get("sourceIP")
        src_mac = data.get("sourceMAC")
        dst_ip = data.get("destIP")
        dst_mac = data.get("destMAC")
        location = data.get("packetlocation")
        return hash((src_ip, src_mac, dst_ip, dst_mac, location))

    def get_link_widget(self, link_name):
        link_data = self.app.ui.get_link(link_name)
        return self.app.get_widget_by_hostname(link_data.get("hostname"))

    def update_packets(self, *args):
        """Updates drawn packet widgets in the puzzle, either by adding new ones,
        changing their locations, or by removing them.
        """

        # Ppacket draw index needs to be above link lines but below devices,
        # which means it needs to be one less than the lowest link index, which
        # can change during the course of solving the puzzle if links are added
        # or removed.
        packet_idx = self.app.get_first_link_index() - 1

        # Remove expired packets.
        for p in self.gui_packets:
            if p.hash_id not in [h for h in self.packet_ids]:
                self.app.root.ids.layout.remove_widget(p)

        # Add or update packets in layout.
        for p in self.app.ui.packetlist:
            link = self.get_link_widget(p.get("packetlocation"))
            # NOTE: Sometimes the layout doesn't contain the link widgets, maybe
            # due to a race condition with a redraw? So skipping packet update
            # if the link isn't found seems to work for now.
            if not link:
                logging.warning(f"Packets: link not found: {p.get('packetlocation')}")
                continue

            # Search for existing packet in layout.
            packet = self.get_gui_packet(p)
            if packet:
                # Remove from layout before updating positiona and index.
                # NOTE: Removing and re-adding allows the draw index to be
                # updated so that the packet sits on top of the link.
                self.app.root.ids.layout.remove_widget(packet)
            else:
                # Create new packet.
                packet = Packet(hash_id=self.get_hash_id(p))

            # Calculate packet position.
            progress = p.get("packetDistance")
            if p.get("packetDirection") == 2:
                progress = 100 - progress
            center_x, center_y = link.get_progress_pos(progress)

            # Add packet to layout at correct position.
            packet.pos = (
                center_x - self.app.PACKET_DIMS[0] / 2,
                center_y - self.app.PACKET_DIMS[1] / 2,
            )
            self.app.root.ids.layout.add_widget(packet, packet_idx)


class Packet(Widget):
    hash_id = NumericProperty()
