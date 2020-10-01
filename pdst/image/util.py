import logging
from itertools import combinations
from math import sqrt

import numpy as np
from PIL import Image, ImageColor

from pdst import analysis, parsing

log = logging.getLogger(__name__)


def fitToBounds(original_size, target_bounds):
    log.debug(f"Calculating image resize from {original_size} to fit in bounds {target_bounds}")
    orig_w = original_size[0]
    orig_h = original_size[1]

    max_w = target_bounds[0]
    max_h = target_bounds[1]

    ratio = orig_w / orig_h

    minBounds = min(target_bounds)
    mSq = minBounds * minBounds

    alt_h = sqrt(mSq / ratio)
    alt_w = alt_h * ratio

    new_h = min(max_h, alt_h)
    new_w = new_h * ratio

    if new_w > max_w:
        new_w = min(max_w, alt_w)
        new_h = new_w / ratio

    new_size = (int(new_w), int(new_h))

    log.debug(f"New Size: {new_size}")

    return new_size


def fillBounds(original_size, target_bounds):
    log.debug(f"Calculating image resize from {original_size} to fill bounds {target_bounds}")
    orig_w = original_size[0]
    orig_h = original_size[1]

    fill_w = target_bounds[0]
    fill_h = target_bounds[1]

    ratio = orig_w / orig_h

    new_h = fill_h
    new_w = new_h * ratio

    if new_w < fill_w:
        new_w = fill_w
        new_h = new_w / ratio

    new_size = (int(new_w), int(new_h))

    log.debug(f"New Size: {new_size}")

    return new_size


def calculateTopLeftCentered(bounds, centerX, centerY):
    return int(centerX - (bounds[0] / 2)), int(centerY - (bounds[1] / 2))


def getLightness(color):
    return (min(color) + max(color)) / 2 if color is not None else 0


def withAlpha(color, alpha):
    if isinstance(alpha, float):
        alpha = min(255, max(0, round(alpha * 255)))

    return color[0], color[1], color[2], alpha


def transparentCopy(image):
    newImage = image.copy()
    transparent = image.copy()
    transparent.putalpha(0)
    mask = image if image.mode == 'RGBA' else None
    newImage.paste(transparent, mask=mask)
    return newImage


def paste2(img1, img2, offset=(0, 0)):
    alphaMask = img2 if img2.mode == 'RGBA' else None
    imgBase = transparentCopy(img1)
    imgBase.paste(img2, offset, alphaMask)
    return Image.alpha_composite(img1, imgBase)


def rgbToYuv(rgbColor):
    toYuv = np.array([[0.299, 0.587, 0.114],
                      [-0.14714119, -0.28886916, 0.43601035],
                      [0.61497538, -0.51496512, -0.10001026]])

    rgbArr = np.array(rgbColor)
    return rgbArr.dot(toYuv)


def yuvToRgb(yuvColor):
    toRgb = np.array([[1, 0, 1.13983],
                      [1, -0.39465, -0.58060],
                      [1, 2.03211, 0]])

    yuvArr = np.array(yuvColor)
    return yuvArr.dot(toRgb)


def getColorDifference(color1, color2):
    if isinstance(color1, str):
        color1 = ImageColor.getrgb(f'#{color1}')

    if isinstance(color2, str):
        color2 = ImageColor.getrgb(f'#{color2}')

    rgb1 = np.array(color1)
    rgb2 = np.array(color2)

    return np.linalg.norm(rgb1 - rgb2)


def getColorDifference2(color1, color2):
    if isinstance(color1, str):
        color1 = ImageColor.getrgb(f'#{color1}')

    if isinstance(color2, str):
        color2 = ImageColor.getrgb(f'#{color2}')

    yuv1 = rgbToYuv(color1)
    yuv2 = rgbToYuv(color2)

    return np.linalg.norm(yuv1 - yuv2)


def colorsTooSimilar(color1, color2):
    yuvDiff = round(getColorDifference2(color1, color2))
    rgbDiff = round(getColorDifference(color1, color2))

    return yuvDiff < 50 or rgbDiff < 60


def changeSimilarBgColors(imageSpecs):
    """
    Changes (if necessary) the background color in the given imageSpecs so that any
    solid backgrounds don't have too similar colors
    """
    bgColors = []
    for imageSpec in imageSpecs:
        currentColor = imageSpec.colors[0]

        if len(bgColors) == 0:
            bgColors.append(currentColor)
            continue

        if imageSpec.isLogo and (imageSpec.bg is None or imageSpec.bg == 'solid'):
            bgColor = getAcceptableColor(imageSpec, bgColors)
            if bgColor is None:
                continue

            bgColors.append(bgColor)

            if bgColor != currentColor:
                imageSpec.colors = [bgColor] + imageSpec.colors
                imageSpec.invert = False


def getAcceptableColor(imageSpec, otherColors):
    """
    Given an imageSpec and a list of existing other colors, find a color from the imageSpec
    that is dissimilar from all other colors given
    """
    imageAnalyzed = False
    potentialColors = imageSpec.colors
    colorOk = False
    i = 0
    checkColor = None
    while not colorOk:
        checkColor = potentialColors[i]
        colorOk = True

        for otherColor in otherColors:
            if colorsTooSimilar(checkColor, otherColor):
                colorOk = False
                i += 1
                if i >= len(potentialColors):
                    if not imageAnalyzed:
                        imageAnalyzed = True
                        analyzedColors, pcts = analysis.getAllColors(imageSpec.imageFile)
                        bw = ['eee', 'fff', '111', '000']
                        potentialColors += analyzedColors + bw
                    else:  # if we reach here, there are no 'good' possible colors
                        return None

    return checkColor


def getColorsForImage(imagePath):
    colorHints = parsing.getAllColorsFromFilename(imagePath)
    if colorHints is not None:
        log.debug(f"Got color hints: {colorHints}")
        return colorHints
    else:
        log.debug("filename parsing failed")
        (foundColors, pcts) = analysis.getAllColors(imagePath)
        if len(foundColors) > 0:
            return foundColors
        else:
            log.debug("didn't get any colors from analyzing image")
            return None
