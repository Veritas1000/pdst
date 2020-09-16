import unittest

from parameterized import parameterized

from pdst import analysis


class TestMetadata(unittest.TestCase):

    @parameterized.expand([
        ([0, 0, 0, 0], [0, 0, 0, 0], True),
        ([0, 1, 0, 0], [1, 0, 0, 0], True),
        ([0, 0, 0, 255], [0, 0, 0, 0], False),
        ([0, 1, 0, 0], [1, 0, 1, 1], True),
        ([0, 0, 0, 255], [5, 5, 0, 255], False),
        ([0, 0, 0], [5, 5, 0], False),
        ([0, 0, 0], [0, 0, 0, 0], True),
    ])
    def test_nearlyEqual(self, arr1, arr2, expected):
        self.assertEqual(expected, analysis.nearlyEqual(arr1, arr2))

    @parameterized.expand([
        ([[0, 0, 0, 0]], [100], [[0, 0, 0, 0]], [100]),
        ([[0, 0, 0, 0], [0, 0, 0, 0]], [100, 100],
         [[0, 0, 0, 0]], [200]),
        ([[0, 0, 0, 0], [255, 255, 255, 255], [1, 1, 1, 0]], [100, 100, 100],
         [[0, 0, 0, 0], [255, 255, 255, 255]], [200, 100]),
    ])
    def test_mergeSimilar(self, inColors, inCounts, expectedColors, expectedCounts):
        outColors, outCounts = analysis.mergeSimilar(inColors, inCounts)

        self.assertEqual(expectedColors, outColors)
        self.assertEqual(expectedCounts, outCounts)

    @parameterized.expand([
        ([0, 0, 0, 0], False, False),
        ([0, 0, 0, 0], True, False),
        ([0, 0, 0, 255], False, True),
        ([0, 0, 0, 255], True, False),
        ([16, 16, 16, 255], True, False),
        ([17, 17, 17, 255], True, True),
        ([238, 238, 238, 255], True, True),
        ([239, 239, 239, 255], True, False),
        ([255, 255, 255, 255], True, False),
    ])
    def test_isColorAcceptable(self, color, noBlackWhite, expected):
        acceptable = analysis.isColorAcceptable(color, noBlackWhite)

        self.assertEqual(expected, acceptable)

    def test_isValidImage_nonImage(self):
        self.assertFalse(analysis.isValidImage(__file__))
