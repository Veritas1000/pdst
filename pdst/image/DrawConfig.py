import logging

from PIL import ImageColor, Image

from pdst import parsing, analysis
from pdst.image import generators, util
from pdst.image.spec import StrokeSpec, ColorOverlaySpec
from pdst.image.util import fitToBounds, getLightness

log = logging.getLogger(__name__)


class LogoDrawConfig:

    def __init__(self, imageSpec, logoBounds, logoCenterXY, defaultColor='#111'):
        self.defaultColor = defaultColor
        self.imageSpec = imageSpec
        self.logoBounds = logoBounds
        self.logoCenterXY = logoCenterXY

        self.logoImage = None
        self.logoResizedDimensions = None

        if imageSpec.colors is None or len(imageSpec.colors) == 0:
            self.colors = self.__getColors(imageSpec.imageFile)
        else:
            self.colors = imageSpec.colors

        bg = imageSpec.bg
        if bg is None:
            bg = parsing.getBgPatternHint(imageSpec.imageFile)

        self.bgGenerator = generators.bgGenFromString(bg)
        self.resizeFunction = fitToBounds

        if imageSpec.invert is None:
            self.invertLogo = parsing.isColorInverted(imageSpec.imageFile)
        else:
            self.invertLogo = imageSpec.invert

    def getLogoImage(self):
        if self.logoImage is None:
            self.logoImage = Image.open(self.imageSpec.imageFile)

        return self.logoImage

    def getLogoResizedSize(self):
        if self.logoResizedDimensions is None:
            self.logoResizedDimensions = self.resizeFunction(self.getLogoImage().size, self.logoBounds)
        return self.logoResizedDimensions

    def __getColors(self, imagePath):
        log.debug(f"Trying to get colors from {imagePath}")

        if imagePath is None:
            log.debug(f"NO IMAGE! using {self.defaultColor}")
            return [self.defaultColor]
        else:
            foundColors = util.getColorsForImage(imagePath)
            if foundColors is not None and len(foundColors) > 0:
                return foundColors
            else:
                log.debug("didn't get any colors from analyzing image")
                return [self.defaultColor]

    def getColorHex(self, position):
        if position >= len(self.colors):
            position = len(self.colors) - 1

        return '#' + self.colors[position]

    def getPrimaryColorHex(self):
        return self.getColorHex(0)

    def getStrokeColor(self):
        strokeSpec = self.imageSpec.strokeSpec
        if strokeSpec is not None and strokeSpec.colorHex is not None:
            strokeColor = ImageColor.getrgb(f"#{strokeSpec.colorHex}")
        else:
            strokeColor = ImageColor.getrgb("#fff")
            if getLightness(ImageColor.getrgb(self.getPrimaryColorHex())) > 128:
                strokeColor = ImageColor.getrgb("#000")

        return strokeColor

    def getStrokeSize(self):
        strokeSpec = self.imageSpec.strokeSpec
        if strokeSpec is not None:
            return strokeSpec.size
        else:
            return 0

    def getStrokeSpec(self):
        return StrokeSpec(self.getStrokeSize(), color=self.getStrokeColor())

    def shouldDrawStroke(self):
        return self.imageSpec.strokeSpec is not None

    def shouldDrawMask(self):
        return self.imageSpec.maskSpec is not None or self.invertLogo

    def getMaskColor(self):
        maskSpec = self.imageSpec.maskSpec
        if maskSpec is not None and maskSpec.colorHex is not None:
            return ImageColor.getrgb(f"#{maskSpec.colorHex}")
        else:
            return self.getStrokeColor()

    def getMaskSpec(self):
        return ColorOverlaySpec(color=self.getMaskColor())
