import unittest

from pdst.image.spec import ImageSpec, StrokeSpec


class TestConfig(unittest.TestCase):

    def test_ImageSpec_strokeSpec_filename(self):
        spec = ImageSpec("Team_stroke$1$000.png")

        self.assertEqual(1, spec.strokeSpec.size)
        self.assertEqual('000', spec.strokeSpec.colorHex)

    def test_ImageSpec_strokeSpec_override(self):
        spec = ImageSpec("Team_stroke$1$000.png", strokeSpec=StrokeSpec(7, 'fff'))

        self.assertEqual(7, spec.strokeSpec.size)
        self.assertEqual('fff', spec.strokeSpec.colorHex)
