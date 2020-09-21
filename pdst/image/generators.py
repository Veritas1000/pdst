import logging
import re

from PIL import ImageColor, ImageDraw, Image, ImageFilter

from pdst.image.spec import StrokeSpec
from pdst.image.util import fillBounds, calculateTopLeftCentered

log = logging.getLogger(__name__)


def bgGenFromString(string):
    log.debug(f"Getting Background Generator for {string}")

    if string is None or string == 'solid':
        return SolidBgGenerator()

    if string.startswith('vStripe'):
        value = re.search(r'[\d.]+', string)[0]
        return VStripeGenerator(value)

    elif string.startswith('hStripe'):
        value = re.search(r'[\d.]+', string)[0]
        return HStripeGenerator(value)

    elif string.startswith('checker'):
        checkSize = float(re.search(r'[\d.]+', string)[0])
        return CheckerGenerator(checkSize)

    elif string.startswith('pinstripe'):
        value = re.search(r'[\d.]+', string)[0]
        return PinstripeGenerator(value)

    elif string == 'blurzoom':
        return BlurZoomGenerator()

    elif string == 'fillLogo':
        return FillLogoGenerator()

    # TODO: alert the user there wasn't a match?

    return SolidBgGenerator()


class BaseBackgroundGenerator:

    def drawBackground(self, baseImage, drawConfig):
        raise NotImplementedError()

    def fillBg(self, baseImage, colorHex):
        draw = ImageDraw.Draw(baseImage)

        size = baseImage.size

        color = ImageColor.getrgb(colorHex)
        draw.rectangle([0, 0, size[0], size[1]], color)

    def getEvenDividedSplitValues(self, totalSize, center, divisionSize, startFromCenter=True):
        dividerValues = []

        if startFromCenter:
            pos = center - (divisionSize / 2)
            dividerValues.append(round(pos))
            while pos > 0:
                pos -= divisionSize
                dividerValues.append(round(pos))

            pos = center + (divisionSize / 2)

        else:
            pos = 0

        if round(pos) not in dividerValues:
            dividerValues.append(round(pos))
        while round(pos) < totalSize:
            pos += divisionSize
            dividerValues.append(round(pos))

        dividerValues.sort()
        return dividerValues

    def getSplitValues(self, totalSize, center, stripe1Size, stripe2Size, startFromCenter=True):
        dividerValues = []

        if startFromCenter:
            pos = center - (stripe1Size / 2)
            dividerValues.append(round(pos))
            while pos > 0:
                pos -= stripe2Size
                dividerValues.append(round(pos))
                pos -= stripe1Size
                dividerValues.append(round(pos))

            pos = center + (stripe1Size / 2)

        else:
            pos = 0

        if round(pos) not in dividerValues:
            dividerValues.append(round(pos))
        while round(pos) < totalSize:
            pos += stripe2Size
            dividerValues.append(round(pos))
            pos += stripe1Size
            dividerValues.append(round(pos))

        dividerValues.sort()
        return dividerValues


class SolidBgGenerator(BaseBackgroundGenerator):

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())


class VStripeGenerator(BaseBackgroundGenerator):

    def __init__(self, value):
        self.stripeValue = float(value)
        self.useRatioSize = '.' in value

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())

        fullSize = baseImage.size
        draw = ImageDraw.Draw(baseImage)
        secondaryColor = ImageColor.getrgb(drawConfig.getColorHex(1))

        logoSize = drawConfig.getLogoResizedSize()
        centerXY = drawConfig.logoCenterXY

        if self.useRatioSize:
            stripeSize = logoSize[0] * self.stripeValue
            lineXValues = super().getEvenDividedSplitValues(fullSize[0], centerXY[0], stripeSize)

        else:
            stripeSize = fullSize[0] / self.stripeValue
            lineXValues = super().getEvenDividedSplitValues(fullSize[0], centerXY[0], stripeSize, False)

        xIndex = 0
        nX = len(lineXValues)
        drawRect = self.useRatioSize and nX % 4 == 0

        while xIndex < nX - 1:
            x1 = lineXValues[xIndex]
            x2 = lineXValues[xIndex + 1]
            xIndex += 1

            if xIndex == nX - 1:
                x2 += 1

            if drawRect:
                draw.rectangle([x1, 0, x2-1, fullSize[1]], secondaryColor)
            drawRect = not drawRect


class HStripeGenerator(BaseBackgroundGenerator):

    def __init__(self, value):
        self.stripeValue = float(value)
        self.useRatioSize = '.' in value

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())

        fullSize = baseImage.size
        draw = ImageDraw.Draw(baseImage)
        secondaryColor = ImageColor.getrgb(drawConfig.getColorHex(1))

        logoSize = drawConfig.getLogoResizedSize()
        centerXY = drawConfig.logoCenterXY

        if self.useRatioSize:
            stripeSize = logoSize[1] * self.stripeValue
            lineYValues = super().getEvenDividedSplitValues(fullSize[1], centerXY[1], stripeSize)

        else:
            stripeSize = fullSize[1] / self.stripeValue
            lineYValues = super().getEvenDividedSplitValues(fullSize[1], centerXY[1], stripeSize, False)

        index = 0
        nY = len(lineYValues)
        drawRect = self.useRatioSize and nY % 4 == 0

        while index < nY - 1:
            y1 = lineYValues[index]
            y2 = lineYValues[index + 1]
            index += 1

            if index == nY - 1:
                y2 += 1

            if drawRect:
                draw.rectangle([0, y1, fullSize[0], y2-1], secondaryColor)
            drawRect = not drawRect


class CheckerGenerator(BaseBackgroundGenerator):

    def __init__(self, checkerSize):
        self.checkerSize = checkerSize

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())
        fullSize = baseImage.size
        draw = ImageDraw.Draw(baseImage)
        secondaryColor = ImageColor.getrgb(drawConfig.getColorHex(1))

        logoSize = drawConfig.getLogoResizedSize()
        centerXY = drawConfig.logoCenterXY

        checkSize = min(logoSize) * self.checkerSize

        lineXValues = super().getEvenDividedSplitValues(fullSize[0], centerXY[0], checkSize)
        lineYValues = super().getEvenDividedSplitValues(fullSize[1], centerXY[1], checkSize)

        xIndex = 0
        nX = len(lineXValues)
        nY = len(lineYValues)
        drawRect = (nX - nY) % 4 != 0

        while xIndex < nX - 1:
            x1 = lineXValues[xIndex]
            x2 = lineXValues[xIndex + 1]
            xIndex += 1
            yIndex = 0
            while yIndex < nY - 1:
                y1 = lineYValues[yIndex]
                y2 = lineYValues[yIndex + 1]
                yIndex += 1

                if drawRect:
                    draw.rectangle([x1, y1, x2-1, y2-1], secondaryColor)
                drawRect = not drawRect


class PinstripeGenerator(BaseBackgroundGenerator):

    def __init__(self, spacingPct):
        self.spacingPct = float(spacingPct)

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())

        fullSize = baseImage.size
        draw = ImageDraw.Draw(baseImage)
        secondaryColor = ImageColor.getrgb(drawConfig.getColorHex(1))

        logoSize = drawConfig.getLogoResizedSize()
        centerXY = drawConfig.logoCenterXY

        spacing = logoSize[0] * self.spacingPct
        pinSize = round(logoSize[0] * 0.01)
        lineXValues = super().getSplitValues(fullSize[0], centerXY[0], spacing, pinSize)

        xIndex = 0
        nX = len(lineXValues)
        drawRect = nX % 4 == 0

        while xIndex < nX - 1:
            x1 = lineXValues[xIndex]
            x2 = lineXValues[xIndex + 1]
            xIndex += 1

            if xIndex == nX - 1:
                x2 += 1

            if drawRect:
                draw.rectangle([x1, 0, x2-1, fullSize[1]], secondaryColor)
            drawRect = not drawRect


class BlurZoomGenerator(BaseBackgroundGenerator):

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())

        img = drawConfig.getLogoImage()
        fullSize = fillBounds(img.size, baseImage.size)
        imgResized = img.resize(fullSize, Image.LANCZOS)
        centerXY = drawConfig.logoCenterXY
        imgPosition = calculateTopLeftCentered(fullSize, centerXY[0], centerXY[1])

        logoMask = imgResized if img.mode == 'RGBA' else None
        drawMask = drawConfig.shouldDrawMask()
        if drawMask:
            maskColor = drawConfig.getMaskColor()
            maskImg = Image.new(img.mode, fullSize, maskColor)
            imgResized.paste(maskImg, (0, 0), logoMask)

        blurSize = min(baseImage.size) // 70
        imgBlurred = imgResized.filter(ImageFilter.GaussianBlur(blurSize))

        blurImage = Image.new(baseImage.mode, baseImage.size, (0, 0, 0, 0))
        blurImage.paste(imgBlurred, imgPosition)
        out = Image.blend(baseImage, blurImage, 0.5)

        if not (drawConfig.shouldDrawStroke() or drawConfig.invertLogo):
            drawConfig.imageSpec.strokeSpec = StrokeSpec(1, '888')

        baseImage.paste(out)


class FillLogoGenerator(BaseBackgroundGenerator):

    def drawBackground(self, baseImage, drawConfig):
        super().fillBg(baseImage, drawConfig.getPrimaryColorHex())
        drawConfig.resizeFunction = fillBounds
        drawConfig.logoBounds = baseImage.size
        drawConfig.logoCenterXY = (baseImage.size[0] // 2, baseImage.size[1] // 2)
