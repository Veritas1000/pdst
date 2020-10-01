import unittest
from unittest.mock import patch

from parameterized import parameterized

from pdst.image import util
from pdst.image.spec import ImageSpec


class TestImageService(unittest.TestCase):

    @parameterized.expand([
        ((100, 100),    (100, 100),     (100, 100)),
        ((100, 100),    (80, 80),       (80, 80)),
        ((100, 100),    (140, 140),     (140, 140)),
        ((100, 80),     (50, 50),       (50, 40)),
        ((160, 200),    (100, 140),     (89, 111)),
        ((400, 180),    (120, 112),     (120, 54)),
        ((100, 100), (200, 200), (200, 200)),
        ((200, 200), (100, 100), (100, 100)),
    ])
    def test_fitToBounds(self, inSize, bounds, expected):
        newSize = util.fitToBounds(inSize, bounds)

        self.assertEqual(expected, newSize)

    @parameterized.expand([
        ((100, 100),    (100, 100),     (100, 100)),
        ((100, 100),    (80, 80),       (80, 80)),
        ((100, 100),    (140, 140),     (140, 140)),
        ((100, 50),     (50, 50),       (100, 50)),
        ((100, 100),    (100, 200),     (200, 200)),
        ((200, 200),    (100, 50),      (100, 100)),
    ])
    def test_fillBounds(self, inSize, bounds, expected):
        newSize = util.fillBounds(inSize, bounds)

        self.assertEqual(expected, newSize)

    @parameterized.expand([
        ((100, 100), (50, 50), (0, 0)),
        ((50, 100), (50, 50), (25, 0)),
        ((100, 50), (50, 50), (0, 25)),
    ])
    def test_calculateTopLeftCentered(self, size, center, expected):
        position = util.calculateTopLeftCentered(size, center[0], center[1])

        self.assertEqual(expected, position)

    @parameterized.expand([
        ((0, 0, 0), 0),
        ((255, 255, 255), 255),
        ((0, 128, 255), 127.5),
        ((0, 0, 255), 127.5),
        ((0, 255, 255), 127.5),
        ((255, 0, 255), 127.5),
    ])
    def test_getLightness(self, color, expected):
        lightness = util.getLightness(color)

        self.assertEqual(expected, lightness)

    @parameterized.expand([
        ((0, 0, 0), 0, 0),
        ((1, 2, 3), 255, 255),
        ((1, 2, 3), 0.5, 128),
        ((1, 2, 3), 1.0, 255),
    ])
    def test_withAlpha(self, color, alpha, expectedAlpha):
        out = util.withAlpha(color, alpha)

        self.assertEqual(color[0], out[0])
        self.assertEqual(color[1], out[1])
        self.assertEqual(color[2], out[2])
        self.assertEqual(expectedAlpha, out[3])

    @parameterized.expand([
        (['fff'], ['00f'], 'fff'),
        (['00f', 'f00'], ['00f'], 'f00'),
        (['fff'], [], 'fff'),
    ])
    def test_getAcceptableColor_basic(self, specColors, otherColors, expected):
        imageSpec = ImageSpec(None, isLogo=True, colors=specColors)

        outColor = util.getAcceptableColor(imageSpec, otherColors)

        self.assertEqual(expected, outColor)

    @parameterized.expand([
        (['00f'], ['00f'], ['f00'], 'f00'),
        (['00f'], ['00f'], ['00f'], 'eee'),
        (['00f'], ['00f', 'eee', 'fff', '111', '000'], ['00f'], None),
    ])
    @patch('pdst.analysis.getAllColors')
    def test_getAcceptableColor_analyzed(self, specColors, otherColors, analyzeColors, expected, mockAnalyze):
        imageSpec = ImageSpec(None, isLogo=True, colors=specColors)
        mockAnalyze.return_value = analyzeColors, []

        outColor = util.getAcceptableColor(imageSpec, otherColors)

        self.assertEqual(expected, outColor)

    @parameterized.expand([
        (['00f'], ['f00'], 'f00'),
        (['00f'], ['00f', 'f00'], 'f00'),
    ])
    def test_changeSimilarBgColors_basic(self, spec1Colors, spec2Colors, expectedSpec2Color):
        spec1 = ImageSpec(None, isLogo=True, colors=spec1Colors)
        spec2 = ImageSpec(None, isLogo=True, colors=spec2Colors)

        imageSpecs = [spec1, spec2]
        util.changeSimilarBgColors(imageSpecs)

        self.assertEqual(spec1Colors[0], spec1.colors[0])
        self.assertEqual(expectedSpec2Color, spec2.colors[0])

    @parameterized.expand([
        (['00f'], ['00f'], 'eee', False),
        (['00f'], ['f00'], 'f00', True),
    ])
    @patch('pdst.analysis.getAllColors')
    def test_changeSimilarBgColors_invert(self, spec1Colors, spec2Colors, expectedSpec2Color, expectedSpec2Invert, mockGetAllColors):
        spec1 = ImageSpec(None, isLogo=True, colors=spec1Colors, invert=True)
        spec2 = ImageSpec(None, isLogo=True, colors=spec2Colors, invert=True)

        mockGetAllColors.return_value = spec2Colors, []

        imageSpecs = [spec1, spec2]
        util.changeSimilarBgColors(imageSpecs)

        self.assertEqual(True, spec1.invert)

        self.assertEqual(expectedSpec2Color, spec2.colors[0])
        self.assertEqual(expectedSpec2Invert, spec2.invert)
