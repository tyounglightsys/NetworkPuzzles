from network_puzzles import device
from network_puzzles import parser
from network_puzzles import ui
import unittest


class TestParse(unittest.TestCase):
    def setUp(self):
        self.parser = parser.Parser()

    def test_command_invalid(self):
        cmds = [
            "help",
            "foo bar",
            "",
        ]
        for cmd in cmds:
            self.assertIsNone(self.parser.parse(cmd))

    def test_search_caseinsensitive(self):
        self.assertEqual(
            self.parser.parse("search dhcp"), self.parser.parse("search DHCP")
        )

    def test_search_valid(self):
        cmds = [
            "search dhcp",
            "search DHCP",
            "puzzles vlan",
            "puzzles",
        ]
        for cmd in cmds:
            r = self.parser.parse(cmd)
            self.assertIsInstance(r, dict)
            self.assertTrue(len(r.get("value")) > 0)
            self.assertTrue(r.get("command") in ["puzzles", "search"])

    def test_search_noresults(self):
        cmds = ["search none", "puzzles 999"]
        for cmd in cmds:
            self.assertEqual(0, len(self.parser.parse(cmd).get("value")))


class TestSetValue(unittest.TestCase):
    def setUp(self):
        self.app = ui.CLI()

    def test_device_not_found(self):
        self.app.load_puzzle("Level0_HiddenSwitch")
        self.assertRaises(NameError, self.app.parser.parse, "set pc999 fakeprop")

    def test_invisible(self):
        self.app.load_puzzle("Level0_HiddenSwitch")
        self.assertFalse(self.app.parser.parse("set net_switch1 power off"))

    def test_not_enough_command_args(self):
        self.app.load_puzzle("Level0_HiddenSwitch")
        self.assertRaises(ValueError, self.app.parser.parse, "set pc999")

    def test_power_off(self):
        self.app.load_puzzle("Level0_HiddenSwitch")
        dev_name = "pc0"
        dev_data = self.app.puzzle.device_from_name(dev_name)
        dev = device.Device(dev_data)
        self.assertTrue(dev.powered_on)
        self.app.parser.parse(f"set {dev_name} power off")
        self.assertFalse(dev.powered_on)
