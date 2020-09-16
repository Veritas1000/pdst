import os
import shutil
import unittest

from PIL import Image

from pdst.image import drawing
from pdst.image.spec import OuterGlowSpec, StrokeSpec, DropShadowSpec, ColorOverlaySpec, LayerEffects, LayerSpec
from tests.helpers import verifyImagesEquivalent


class TestImageService(unittest.TestCase):
    testFilesDir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'test-files'))
    outDir = os.path.join(testFilesDir, 'out')
    genRefDir = os.path.join(testFilesDir, 'gen-reference')

    # ONLY for regenerating reference images after an intentional drawing change!
    regen_not_test = False

    @classmethod
    def setUpClass(cls):
        # setup temp output dir
        os.makedirs(cls.outDir)

    @classmethod
    def tearDownClass(cls):
        # cleanup temp out dir
        shutil.rmtree(cls.outDir)

    def test_drawStroke(self):
        alphaImg = os.path.join(self.testFilesDir, 'logos', 'plain', 'Charlie.png')

        logo = Image.open(alphaImg)

        outImg = Image.new('RGB', (logo.size[0] + 50, logo.size[1] + 50), (255, 255, 255))

        strokeSpec = StrokeSpec(20, colorHex='088', opacity=0.4)
        outImg = drawing.drawStroke(outImg, strokeSpec, (25, 25), logo)
        outImg.paste(logo, (25, 25), logo)

        if self.regen_not_test:
            outImg.save('stroke.png')
            return

        testImage = os.path.join(self.outDir, 'stroke.png')
        outImg.save(testImage)

        compareImage = os.path.join(self.genRefDir, 'stroke.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_dropShadow(self):
        alphaImg = os.path.join(self.testFilesDir, 'logos', 'plain', 'Charlie.png')

        logo = Image.open(alphaImg)

        outImg = Image.new('RGB', (logo.size[0] + 50, logo.size[1] + 50), (255, 255, 255))

        spec = DropShadowSpec(10, 30, 35, 0.7)
        outImg = drawing.dropShadow(outImg, spec, (25, 25), logo)
        outImg.paste(logo, (25, 25), logo)

        if self.regen_not_test:
            outImg.save('shadow.png')
            return

        testImage = os.path.join(self.outDir, 'shadow.png')
        outImg.save(testImage)

        compareImage = os.path.join(self.genRefDir, 'shadow.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_outerGlow(self):
        alphaImg = os.path.join(self.testFilesDir, 'logos', 'plain', 'Charlie.png')

        logo = Image.open(alphaImg)

        outImg = Image.new('RGB', (logo.size[0] + 50, logo.size[1] + 50), (26, 26, 26))

        glowSpec = OuterGlowSpec(20, 'aff', 0.8)
        outImg = drawing.outerGlow(outImg, glowSpec, (25, 25), logo)
        outImg.paste(logo, (25, 25), logo)

        if self.regen_not_test:
            outImg.save('outer_glow.png')
            return

        testImage = os.path.join(self.outDir, 'outer_glow.png')
        outImg.save(testImage)

        compareImage = os.path.join(self.genRefDir, 'outer_glow.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_colorOverlay(self):
        alphaImg = os.path.join(self.testFilesDir, 'logos', 'plain', 'Charlie.png')

        logo = Image.open(alphaImg)

        outImg = Image.new('RGB', (logo.size[0] + 50, logo.size[1] + 50), (26, 26, 26))

        spec = ColorOverlaySpec('ffa', 0.5)
        outImg.paste(logo, (25, 25), logo)
        outImg = drawing.colorOverlay(outImg, spec, (25, 25), logo)

        if self.regen_not_test:
            outImg.save('color_overlay.png')
            return

        testImage = os.path.join(self.outDir, 'color_overlay.png')
        outImg.save(testImage)

        compareImage = os.path.join(self.genRefDir, 'color_overlay.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)

    def test_drawLayerSpec(self):
        alphaImg = os.path.join(self.testFilesDir, 'logos', 'plain', 'Charlie.png')

        logo = Image.open(alphaImg)

        outImg = Image.new('RGB', (logo.size[0] + 50, logo.size[1] + 50), (180, 230, 190))

        stroke = StrokeSpec(4, colorHex='222', opacity=0.7)
        shadow = DropShadowSpec(10, 30, 35, 0.7)
        glow = OuterGlowSpec(20, 'f88', 0.8)
        mask = ColorOverlaySpec('fff', 0.3)

        layerEffects = LayerEffects(stroke=stroke, colorOverlay=mask, outerGlow=glow, dropShadow=shadow)
        layerSpec = LayerSpec(logo, (25, 25), layerEffects)
        outImg = drawing.drawLayerSpec(outImg, layerSpec)

        if self.regen_not_test:
            outImg.save('layer_spec.png')
            return

        testImage = os.path.join(self.outDir, 'layer_spec.png')
        outImg.save(testImage)

        compareImage = os.path.join(self.genRefDir, 'layer_spec.png')

        (match, msg) = verifyImagesEquivalent(compareImage, testImage, 5)

        if not match:
            self.fail(msg)
