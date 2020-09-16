import unittest
from unittest.mock import MagicMock

from pdst.image.compositor import SimpleCompositor, SingleImageCompositor
from pdst.image.spec import CompositeSpec


class TestCompositor(unittest.TestCase):
    mockImageSpec = MagicMock()
    basicCompositeSpec = CompositeSpec((100, 100))

    def test_SimpleCompositor_numParts(self):
        c = SimpleCompositor(self.basicCompositeSpec, [self.mockImageSpec, self.mockImageSpec])
        self.assertEqual(2, c.numParts)

    def test_SimpleCompositor_partFullSize(self):
        c = SimpleCompositor(self.basicCompositeSpec, [self.mockImageSpec, self.mockImageSpec])

        self.assertEqual((58, 100), c.getPartFullSize(0))
        self.assertEqual((58, 100), c.getPartFullSize(1))

    def test_SimpleCompositor_partSafeBounds(self):
        c = SimpleCompositor(self.basicCompositeSpec, [self.mockImageSpec, self.mockImageSpec])

        left = c.getPartSafeBounds(0)
        right = c.getPartSafeBounds(1)

        self.assertEqual(((0, 0), (47, 100)), left)
        self.assertEqual(((11, 0), (47, 100)), right)

    def test_SimpleCompositor_getPartTopLeft(self):
        c = SimpleCompositor(self.basicCompositeSpec, [self.mockImageSpec, self.mockImageSpec])

        left = c.getPartTopLeft(0)
        right = c.getPartTopLeft(1)

        self.assertEqual((0, 0), left)
        self.assertEqual((42, 0), right)

    def test_SingleImageCompositor_numParts(self):
        c = SingleImageCompositor(self.basicCompositeSpec, self.mockImageSpec)
        self.assertEqual(1, c.numParts)

    def test_SingleImageCompositor_partFullSize(self):
        c = SingleImageCompositor(self.basicCompositeSpec, self.mockImageSpec)

        self.assertEqual((100, 100), c.getPartFullSize(0))

    def test_SingleImageCompositor_partSafeBounds(self):
        c = SingleImageCompositor(self.basicCompositeSpec, self.mockImageSpec)

        safe = c.getPartSafeBounds(0)

        self.assertEqual(((0, 0), (100, 100)), safe)

    def test_SingleImageCompositor_getPartTopLeft(self):
        c = SingleImageCompositor(self.basicCompositeSpec, self.mockImageSpec)

        tl = c.getPartTopLeft(0)

        self.assertEqual((0, 0), tl)
