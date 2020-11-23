import unittest

from main import construct_ipv4


class ConfigTest(unittest.TestCase):
    def test_ip4_construct(self):
        self.assertEqual(
            construct_ipv4('172.30.128.20', 2),
            '172.30.128.22'
        )
        self.assertEqual(
            construct_ipv4('172.16.1.0', 1),
            '172.16.1.1'
        )

    def test_ip4_construct_withstr(self):
        self.assertEqual(
            construct_ipv4('172.30.128.24', '1'),
            '172.30.128.25'
        )


if __name__ == '__main__':
    unittest.main()
