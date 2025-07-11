import json
import unittest
from network_puzzles import device
from network_puzzles import session
from network_puzzles import ui
from . import PUZZLES_DIR


class TestDeviceProperties(unittest.TestCase):
    def setUp(self):
        self.app = ui.CLI()

    def test_is_invisible(self):
        self.app.load_puzzle("Level0_HiddenSwitch")
        # Test not invisible.
        self.assertFalse(device.Device("net_switch0").is_invisible)
        # Test invisible.
        self.assertTrue(device.Device("net_switch1").is_invisible)

    def test_powered_on(self):
        self.app.load_puzzle("Level0_HubVsSwitch")
        dev = device.Device("pc0")
        # Test undefined.
        self.assertTrue(dev.powered_on)
        # Test powered on.
        dev.json["poweroff"] = "False"
        self.assertTrue(dev.powered_on)
        # Test powered off.
        dev.json["poweroff"] = "True"
        self.assertFalse(dev.powered_on)


class TestGetDeviceAttribs(unittest.TestCase):
    def setUp(self):
        self.data = {"a": "all", "g": "good", "hostname": "test"}

        # TODO: Use Mock rather than "real" session.puzzle.
        self.puzzle_name = "Level0_HubVsSwitch"
        self.hostname = "pc0"

        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f"{self.puzzle_name}.json"
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get("EduNetworkBuilder").get("Network")
        self.device_json = None
        devices = self.network.get("device")
        for d in devices:
            if d.get("hostname") == self.hostname:
                self.device_json = d

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle
        self.device = device.Device(self.hostname)

    def test_allnics(self):
        self.assertEqual(len(self.device.all_nics()), len(self.device_json.get("nic")))

    def test_alltests(self):
        puzzle_tests = self.network.get("nettest")
        device_tests = [t for t in puzzle_tests if t.get("shost") == self.hostname]
        self.assertEqual(len(self.device.all_tests()), len(device_tests))

    def test_hostname(self):
        self.assertEqual(self.data.get("hostname"), device.Device(self.data).hostname)


class TestGetItemByAttrib(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"name": "item1", "uid": "0"},
            {"name": "item2", "uid": "1"},
        ]

        # TODO: Use Mock rather than "real" session.puzzle.
        self.puzzle_name = "Level0_HubVsSwitch"

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle

    def test_found(self):
        self.assertEqual(
            self.items[0], session.puzzle._item_by_attrib(self.items, "name", "item1")
        )

    def test_notfound(self):
        self.assertIsNone(session.puzzle._item_by_attrib(self.items, "uid", "3"))


class TestXFromY(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = "Level0_HubVsSwitch"

        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f"{self.puzzle_name}.json"
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get("EduNetworkBuilder").get("Network")

        self.device0 = self.network.get("device")[0]  # net_hub0
        self.nic00 = self.device0.get("nic")[0]

    def test_maclist_fromdevice(self):
        self.assertEqual(
            len([n for n in self.device0.get("nic") if n.get("nicname") != "lo0"]),
            len(device.Device(self.device0).mac_list()),
        )

    def test_maclist_fromhostname(self):
        self.assertEqual(
            len([n for n in self.device0.get("nic") if n.get("nicname") != "lo0"]),
            len(device.Device("net_hub0").mac_list()),
        )

    def test_nicfromname_withdevice_found(self):
        self.assertEqual(self.nic00, device.Device(self.device0).nic_from_name("lo0"))

    def test_nicfromname_withdevice_notfound(self):
        self.assertIsNone(device.Device(self.device0).nic_from_name("eth99"))

    def test_nicfromname_withhostname_found(self):
        self.assertEqual(
            self.nic00.get("uniqueidentifier"),
            device.Device("net_hub0").nic_from_name("lo0").get("uniqueidentifier"),
        )

    def test_nicfromname_withhostname_notfound(self):
        self.assertIsNone(device.Device("not_exist").nic_from_name("lo0"))

    def test_nicfromname_withuid_found(self):
        self.assertEqual(
            self.nic00.get("uniqueidentifier"),
            device.Device("160").nic_from_name("lo0").get("uniqueidentifier"),
        )

    def test_nicfromname_withuid_notfound(self):
        self.assertIsNone(device.Device("not_exist").nic_from_name("lo0"))
