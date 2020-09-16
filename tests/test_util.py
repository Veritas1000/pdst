import unittest

from pdst import util


class TestUtil(unittest.TestCase):

    def test_removeNones(self):
        one = util.removeNones(('a', 'b', None, 'c'))
        self.assertEqual(['a', 'b', 'c'], one)

        two = util.removeNones([None, 'a', None, None, 'b', None, 'c'])
        self.assertEqual(['a', 'b', 'c'], two)