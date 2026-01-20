import json
import unittest

from network_puzzles import nic, ui

from . import PUZZLES_DIR


class TestNicProperties(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = "Level0_Ping"
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)
        fpath = PUZZLES_DIR / f"{self.puzzle_name}.json"
        with fpath.open() as f:
            self.data = json.load(f).get("EduNetworkBuilder").get("Network")

    def test_nic_ifaces_listing(self):
        # Ensure that single interface item is correctly changed to a single-item list.
        dev_idx = 0  # laptop0
        nic_idx = 0  # lo0
        nic_uid = "104"
        json_ifaces = (
            self.data.get("device")[dev_idx].get("nic")[nic_idx].get("interface")
        )
        self.assertTrue(isinstance(json_ifaces, dict))
        self.assertEqual(
            [json_ifaces],
            nic.Nic(self.app.puzzle.nic_from_uid(nic_uid)).interfaces,
        )

    def test_nic_json(self):
        dev_idx = 0
        nic_idx = 0
        nic_uid = "104"
        nic_json = self.data.get("device")[dev_idx].get("nic")[nic_idx]
        app_json = nic.Nic(self.app.puzzle.nic_from_uid(nic_uid)).json
        # Remove extra runtime data.
        del app_json["Mac"]
        self.assertEqual(nic_json, app_json)

    def test_nic_myid(self):
        dev_idx = 0
        nic_idx = 0
        nic_uid = "104"
        myid_json = self.data.get("device")[dev_idx].get("nic")[nic_idx].get("myid")
        app_json = nic.Nic(self.app.puzzle.nic_from_uid(nic_uid)).my_id.json
        self.assertEqual(myid_json, app_json)

    """
    def test_link_ct(self):
        self.assertEqual(
            len(self.data.get("link")), len([k for k in self.app.puzzle.links])
        )

    def test_dest(self):
        dests = [link.Link(k).dest for k in self.app.puzzle.links]
        for data_k in self.data.get("link"):
            self.assertTrue(data_k.get("DstNic").get("hostname") in dests)

    def test_hostname(self):
        hostnames = [link.Link(k).hostname for k in self.app.puzzle.links]
        for data_k in self.data.get("link"):
            self.assertTrue(data_k.get("hostname") in hostnames)

    def test_linktype(self):
        broken_link = None
        normal_link = None
        for link_data in self.data.get("link"):
            if link_data.get("hostname") == "router0_link_laptop1":
                broken_link = link_data
            elif link_data.get("hostname") == "laptop0_link_net_switch0":
                normal_link = link_data
        self.assertIsNotNone(broken_link)
        self.assertIsNotNone(normal_link)
        self.assertEqual(link.Link(broken_link).linktype, "broken")
        self.assertEqual(link.Link(normal_link).linktype, "normal")

    def test_src(self):
        srcs = [link.Link(k).src for k in self.app.puzzle.links]
        for data_k in self.data.get("link"):
            self.assertTrue(data_k.get("SrcNic").get("hostname") in srcs)
    """
