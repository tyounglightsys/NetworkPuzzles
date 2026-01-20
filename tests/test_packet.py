import unittest

from network_puzzles import device, nic, ui


class TestPackets(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = "Level0_Ping"
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)

    def test_ping(self):
        src = "pc0"
        src_ips = []
        for n in device.Device(self.app.puzzle.device_from_name(src)).all_nics():
            for a in nic.Nic(n).ip_addresses:
                src_ips.append(a.get("ip"))
        dst = "net_switch0"
        dst_ips = []
        for n in device.Device(self.app.puzzle.device_from_name(dst)).all_nics():
            for a in nic.Nic(n).ip_addresses:
                dst_ips.append(a.get("ip"))
        command = f"ping {src} {dst}"
        self.app.parser.parse(command)
        pkt = self.app.puzzle.packets[0]
        self.assertEqual(len(self.app.puzzle.packets), 1)
        self.assertEqual(pkt.status, "good")
        self.assertEqual(pkt.packet_location, "pc0_link_net_switch0")
        self.assertEqual(pkt.distance, 0)
        ping_started = False
        response_started = False
        while self.app.puzzle.packets_need_processing():
            self.app.puzzle.process_packets(2)
            for p in self.app.puzzle.packets:
                # If packet source_ip is in src dev IPs, consider the ping started.
                if str(p.source_ip).split("/")[0] in src_ips:
                    if not ping_started and p.status == "good":
                        ping_started = True
                # If packet source_ip is in dst dev IPs, consider the response started.
                if str(p.source_ip).split("/")[0] in dst_ips:
                    if not response_started and p.status == "good":
                        response_started = True
        self.assertTrue(ping_started)
        self.assertTrue(response_started)
