from network_puzzles import parser
import unittest


class TestParse(unittest.TestCase):
    def test_command_invalid(self):
        cmds = [
            'help',
            'foo bar',
            '',
        ]
        for cmd in cmds:
            self.assertIsNone(parser.parse(cmd))

    def test_search_caseinsensitive(self):
        self.assertEqual(parser.parse('search dhcp'), parser.parse('search DHCP'))

    def test_search_valid(self):
        cmds = [
            'search dhcp',
            'search DHCP',
            'puzzles vlan',
            'puzzles',
        ]
        for cmd in cmds:
            r = parser.parse(cmd)
            self.assertIsInstance(r, dict)
            self.assertTrue(len(r.get('value')) > 0)
            self.assertTrue(r.get('command') in ['puzzles', 'search'])
    
    def test_search_noresults(self):
        cmds = [
            'search none',
            'puzzles 999'
        ]
        for cmd in cmds:
            self.assertEqual(0, len(parser.parse(cmd).get('value')))