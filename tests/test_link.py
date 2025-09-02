import json
import unittest
from network_puzzles import link
from network_puzzles import ui
from . import PUZZLES_DIR


class TestLinkProperties(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = "Level0_BrokenLink"
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)
        fpath = PUZZLES_DIR / f"{self.puzzle_name}.json"
        with fpath.open() as f:
            self.data = json.load(f).get("EduNetworkBuilder").get("Network")

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
