import logging

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from pdst.image.DrawConfig import LogoDrawConfig
from pdst.image.compositor import SimpleCompositor, SingleImageCompositor
from pdst.image.drawing import drawLayers
from pdst.image.spec import LayerEffects, LayerSpec, LayerGroupSpec, DropShadowSpec
from pdst.image.util import calculateTopLeftCentered

log = logging.getLogger(__name__)


class ImageGenerator:

    def __init__(self, config):
        self.config = config
        self.thumbnailSize = config.thumbnailSize
        self.fallbackColor = config.fallbackColor

    def generateImage(self, compositeSpec, imageSpecs):
        numImages = len(imageSpecs)
        if numImages == 0:
            return None
        elif numImages == 1:
            compositor = SingleImageCompositor(compositeSpec, imageSpecs[0])
        elif numImages == 2:
            compositor = SimpleCompositor(compositeSpec, imageSpecs)
        else:
            raise NotImplementedError("Don't know how to draw a composition with more than 2 images!")

        img = self.__drawComposite(compositor)
        img = self.__drawText(img, compositor)

        return img

    def __drawComposite(self, compositor):
        bgColor = ImageColor.getrgb('#' + self.fallbackColor)
        baseImage = Image.new("RGB", compositor.size, bgColor)

        specs = []
        for i in range(0, compositor.numParts):
            imagePartSize = compositor.getPartFullSize(i)
            safeBounds = compositor.getPartSafeBounds(i)
            logoGroup = self.__drawLogoAndBackground(compositor.partSpecs[i], imagePartSize, safeBounds)
            mask = compositor.getPartMask(i)
            logoGroup.alphaMask = mask
            logoGroup.offset = compositor.getPartTopLeft(i)
            specs.append(logoGroup)

        outImage = drawLayers(baseImage, specs)
        return outImage

    def __drawLogoAndBackground(self, imageSpec, fullBounds, safeBounds=None):
        """Returns an Image of size fullBounds with the logo and its background"""
        if safeBounds is None:
            safeBounds = ((0, 0), fullBounds)

        # draw logo centered in the safe bounds
        logoSafeW = safeBounds[1][0]
        logoSafeH = safeBounds[1][1]

        log.debug(f"safe width/height: {logoSafeW},{logoSafeH}")

        logoBounds = (int(logoSafeW * 0.8), int(logoSafeH * 0.75))
        logoCenterX = int(safeBounds[0][0] + (logoSafeW / 2))
        logoCenterY = int(safeBounds[0][1] + (logoSafeH / 2))

        log.debug(f"Logo center X/Y: {logoCenterX},{logoCenterY}")
        logoCenterXY = (logoCenterX, logoCenterY)

        logoDrawCfg = LogoDrawConfig(imageSpec, logoBounds, logoCenterXY, self.config.fallbackColor)

        bgColor = ImageColor.getrgb(logoDrawCfg.getPrimaryColorHex())
        baseImage = Image.new("RGB", fullBounds, bgColor)

        # Draw background pattern (if applicable)
        if logoDrawCfg.bgGenerator is not None:
            logoDrawCfg.bgGenerator.drawBackground(baseImage, logoDrawCfg)

        backgroundLayerSpec = LayerSpec(baseImage)
        logoLayerSpec = self.__getLayerSpec(logoDrawCfg)

        return LayerGroupSpec([backgroundLayerSpec, logoLayerSpec])

    def __getLayerSpec(self, drawCfg):
        logo = drawCfg.getLogoImage()
        logoSize = drawCfg.getLogoResizedSize()
        logoResized = logo.resize(logoSize, Image.LANCZOS)
        centerXY = drawCfg.logoCenterXY
        logoPosition = calculateTopLeftCentered(logoSize, centerXY[0], centerXY[1])

        stroke = None
        if drawCfg.shouldDrawStroke():
            stroke = drawCfg.getStrokeSpec()
        mask = None
        if drawCfg.shouldDrawMask():
            mask = drawCfg.getMaskSpec()

        layerEffects = LayerEffects(stroke=stroke, colorOverlay=mask)
        spec = LayerSpec(logoResized, logoPosition, layerEffects)

        return spec

    def __drawText(self, image, compositor):
        text = compositor.compositeSpec.text
        log.debug(f"Drawing text: {text}")
        if text is None:
            return image

        withAlpha = image.convert('RGBA')
        # background banner
        bannerRect = compositor.textBgRect

        # Blurred underlay
        blurSize = min(image.size) // 50
        blurred = withAlpha.copy().filter(ImageFilter.GaussianBlur(blurSize))
        cropped = blurred.crop(bannerRect)
        blurImage = Image.new("RGBA", withAlpha.size, (255, 255, 255, 0))
        blurImage.paste(cropped, bannerRect)
        withBlur = Image.alpha_composite(withAlpha, blurImage)

        # Drop shadow
        shadowImage = Image.new("RGBA", withAlpha.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadowImage)
        shadowRect = bannerRect
        draw.rectangle(shadowRect, fill=(0, 0, 0, 20))
        shadowBlur = shadowImage.filter(ImageFilter.GaussianBlur(blurSize))
        withShadow = Image.alpha_composite(withBlur, shadowBlur)

        # Banner + Text
        txtImage = Image.new("RGBA", withAlpha.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txtImage)
        draw.rectangle(bannerRect, fill=(255, 255, 255, 120))
        draw.text(compositor.textDrawPos, text, font=compositor.font, fill=(17, 17, 17))

        out = Image.alpha_composite(withShadow, txtImage)
        return out
