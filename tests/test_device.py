import json
import unittest
from network_puzzles import device
from network_puzzles import session
from network_puzzles import ui
from . import PUZZLES_DIR


class TestAllDevicesAndLinks(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_alldevices(self):
        pass

    @unittest.skip("not implemented")
    def test_alllinks(self):
        pass


class TestGetItemByAttrib(unittest.TestCase):
    def setUp(self):
        self.items = [
            {'name': 'item1', 'uid': '0'},
            {'name': 'item2', 'uid': '1'},
        ]

        # TODO: Use Mock rather than "real" session.puzzle.
        self.puzzle_name = 'Level0-HubVsSwitch'

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle
    
    def test_found(self):
        self.assertEqual(self.items[0], session.puzzle._item_by_attrib(self.items, 'name', 'item1'))

    def test_notfound(self):
        self.assertIsNone(session.puzzle._item_by_attrib(self.items, 'uid', '3'))


class TestXFromY(unittest.TestCase):
    def setUp(self):
        self.puzzle_name = 'Level0-HubVsSwitch'

        # Load puzzle via app in to session.puzzle.
        self.app = ui.CLI()
        self.app.load_puzzle(self.puzzle_name)  # sets session.puzzle

        # Load puzzle data separately via json.load.
        puzzle_file = PUZZLES_DIR / f'{self.puzzle_name}.json'
        with puzzle_file.open() as f:
            self.puzzle = json.load(f)  # gets independent puzzle data from file
        self.network = self.puzzle.get('EduNetworkBuilder').get('Network')
        self.device0 = self.network.get('device')[0]  # net_hub0
        self.nic00 = self.device0.get('nic')[0]
        self.device1 = self.network.get('device')[1]  # net_switch0
        self.device4 = self.network.get('device')[4]  # router0
        self.link0 = self.network.get('link')[0]  # link between net_switch0 and router0

    def test_devicefromid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_uid('160').get('uniqueidentifier')
        )

    def test_devicefromid_notfound(self):
        self.assertIsNone(session.puzzle.device_from_uid('999'))

    def test_devicefromname_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.device_from_name('net_hub0').get('uniqueidentifier')
        )

    def test_devicefromname_notfound(self):
        self.assertIsNone(session.puzzle.device_from_name('supercool_dev9'))

    def test_itemfromid_found(self):
        self.assertEqual(
            self.device0.get('uniqueidentifier'),
            session.puzzle.item_from_uid('160').get('uniqueidentifier')
        )

    def test_itemfromid_notfound(self):
        self.assertIsNone(session.puzzle.item_from_uid('999'))

    def test_linkfromdevices_found(self):
        self.assertEqual(
            self.link0.get('uniqueidentifier'),
            session.puzzle.link_from_devices(self.device1, self.device4).get('uniqueidentifier')
        )

    def test_linkfromdevices_notfound(self):
        self.assertIsNone(session.puzzle.link_from_devices(self.device0, self.device1))

    def test_linkfromid_found(self):
        self.assertEqual(
            self.link0,
            session.puzzle.link_from_uid('146'))

    def test_linkfromid_notfound(self):
        self.assertIsNone(session.puzzle.link_from_uid('999'))

    def test_linkfromname_found(self):
        self.assertEqual(
            self.link0,
            session.puzzle.link_from_name('net_switch0_link_router0'))

    def test_linkfromname_notfound(self):
        self.assertIsNone(session.puzzle.link_from_name('no_such_link'))

    def test_nicfromid_found(self):
        self.assertEqual(
            self.nic00.get('uniqueidentifier'),
            device.nicFromID('161').get('uniqueidentifier')
        )

    def test_nicfromid_notfound(self):
        self.assertIsNone(device.nicFromID('999'))

    def test_nicfromname_found(self):
        self.assertEqual(self.nic00, device.nicFromName(self.device0, 'lo0'))

    def test_nicfromname_notfound(self):
        self.assertIsNone(device.nicFromName(self.device0, 'eth99'))