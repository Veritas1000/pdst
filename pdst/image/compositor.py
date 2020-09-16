import logging

from PIL import Image, ImageDraw, ImageFont

from pdst import filetools

log = logging.getLogger(__name__)


class BaseCompositor:
    def __init__(self, partSpecs, compositeSpec):
        self.partSpecs = partSpecs
        self.numParts = len(partSpecs)
        self.size = compositeSpec.size
        self.compositeSpec = compositeSpec

        text = compositeSpec.text
        self.__initFont(text)

        self.textBounds = (0, 0, 0, 0)
        self.textBgRect = (0, 0, 0, 0)
        self.textDrawPos = (0, 0)

        w = self.size[0]
        h = self.size[1]
        if text is not None:
            self.textBounds = self.font.getmask(text).getbbox()

            textHeight = self.textBounds[3]
            textWidth = self.textBounds[2]

            bannerH = round(textHeight * 1.25)
            bannerBottom = h
            bannerTop = bannerBottom - bannerH
            self.textBgRect = (0, bannerTop, w, bannerBottom)

            textDrawX = (w - textWidth) // 2
            (width, baseline), (offset_x, offset_y) = self.font.font.getsize(text)
            textDrawY = ((bannerTop + bannerBottom) // 2) - (textHeight // 2) - offset_y

            self.textDrawPos = textDrawX, textDrawY

    def getPartFullSize(self, num):
        raise NotImplementedError()

    def getPartSafeBounds(self, num):
        raise NotImplementedError()

    def getPartMask(self, num):
        raise NotImplementedError()

    def getPartTopLeft(self, num):
        raise NotImplementedError()

    def __initFont(self, text):
        fontSize = self.size[1] // 5
        fontFile = filetools.getResourceFilePath('fonts/SourceSansPro-Bold.ttf')
        log.debug(f"font: {fontFile}")
        tempFont = ImageFont.truetype(fontFile, fontSize)

        if text is not None:
            textWidth = tempFont.getmask(text).getbbox()[2]

            maxTextWidth = self.size[0] * 0.95
            while textWidth > maxTextWidth:
                fontSize = int(fontSize * (maxTextWidth / textWidth))
                tempFont = ImageFont.truetype(fontFile, fontSize)
                textWidth = tempFont.getmask(text).getbbox()[2]

        self.font = ImageFont.truetype(fontFile, fontSize)


class SingleImageCompositor(BaseCompositor):
    """Compositor for a single image"""
    def __init__(self, compositeSpec, imageSpec):
        super().__init__([imageSpec], compositeSpec)

    def getPartFullSize(self, num):
        return self.size

    def getPartSafeBounds(self, num):
        safeH = self.size[1] - self.textBounds[3] // 2
        return (0, 0), (self.size[0], safeH)

    def getPartMask(self, num):
        return Image.new('L', self.size, color=255)

    def getPartTopLeft(self, num):
        return 0, 0


class SimpleCompositor(BaseCompositor):
    """Basic two-image compositor that places the images side-by-side with a diagonal divider down the center"""
    def __init__(self, compositeSpec, imageSpecs):
        super().__init__(imageSpecs, compositeSpec)

        w = self.size[0]
        h = self.size[1]
        mid_w = w / 2

        dividerPct = 16
        divider_size = int(w * (dividerPct / 100))
        log.debug(f"divider_size: {divider_size}")

        dividerLX = int(mid_w - (divider_size / 2))
        dividerRX = dividerLX + divider_size

        log.debug(f"divider X: {dividerLX} -> {dividerRX}")

        self.divider_size = divider_size
        self.dividerLX = dividerLX
        self.dividerRX = dividerRX
        self.partSize = (dividerRX, h)
        self.logoUnsafeX = int(divider_size * 0.7)
        self.logoSafeW = dividerRX - self.logoUnsafeX

    def getPartFullSize(self, num):
        return self.partSize

    def getPartSafeBounds(self, num):
        """Returns the 'safe area' for placing a logo as a tuple of (topLeftPointXY, (width, height))"""
        topL = (0 + (num * self.logoUnsafeX), 0)
        safeH = self.size[1] - self.textBounds[3] // 2
        return topL, (self.logoSafeW, safeH)

    def getPartMask(self, num):
        topL = (num * self.divider_size, 0)
        topR = (self.dividerRX, 0)
        botR = (self.dividerLX + (num * self.divider_size), self.size[1])
        botL = (0, self.size[1])

        poly = [topL, topR, botR, botL]
        mask = Image.new('L', self.partSize, color=0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(poly, fill=255)

        # poly = [topL, topR, botR, botL]
        # partTL = self.getPartTopLeft(num)
        # adjusted = []
        # for pt in poly:
        #     adjusted.append((pt[0] + partTL[0], pt[1] + partTL[1]))
        #
        # mask = Image.new('L', self.size, color=0)
        # draw = ImageDraw.Draw(mask)
        # draw.polygon(adjusted, fill=255)

        return mask

    def getPartTopLeft(self, num):
        return num * self.dividerLX, 0
