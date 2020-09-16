import binascii
import logging
import warnings

import numpy
import numpy as np
import scipy
import scipy.cluster
import scipy.misc
from PIL import Image

log = logging.getLogger(__name__)


def isValidImage(path):
    try:
        Image.open(path).verify()
        return True
    except:
        return False


def isColorAcceptable(colorArr, noBlackWhite=False):
    log.debug(f"checking for color acceptability: {colorArr}")

    alpha = colorArr[3] if len(colorArr) > 3 else 255
    alphaGood = alpha > 200

    if noBlackWhite:
        red = colorArr[0]
        green = colorArr[1]
        blue = colorArr[2]

        blackThreshold = 17
        almostBlack = red < blackThreshold and green < blackThreshold and blue < blackThreshold

        whiteThreshold = 238
        almostWhite = red > whiteThreshold and green > whiteThreshold and blue > whiteThreshold

        return alphaGood and not almostBlack and not almostWhite
    else:
        return alphaGood


def arrayToHex(arr):
    return binascii.hexlify(bytearray(round(c) for c in arr)).decode('ascii')[:6]


def codeToIntArray(byteArr):
    return [round(c) for c in byteArr]


def getColorCounts(filename):
    log.debug(f"Finding color occurrence for {filename}")

    im = Image.open(filename)
    if im.mode not in ['RGBA', 'RGB']:
        log.warning(f"Unable to detect colors in {filename} because it is stored with {im.mode} pixel format.")
        return [], []

    NUM_CLUSTERS = 16

    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(numpy.product(shape[:2]), shape[2]).astype(float)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        codes, dist = scipy.cluster.vq.kmeans2(ar, NUM_CLUSTERS, minit='++')
        vecs, dist = scipy.cluster.vq.vq(ar, codes)  # assign codes
        counts, bins = numpy.histogram(vecs, len(codes))  # count occurrences

    log.debug('colors:')
    colors = [codeToIntArray(code) for code in codes]
    log.debug(colors)

    log.debug('counts:')
    log.debug(counts)

    return colors, counts


def mergeSimilar(colors, counts):
    mergedColors = []
    mergedCounts = []
    if len(colors) > 0:
        mergedColors = [colors[0]]
        mergedCounts = [0]

    for i1, color in enumerate(colors):
        foundMatch = False
        for i2, existing in enumerate(mergedColors):
            if nearlyEqual(color, existing):
                mergedCounts[i2] += counts[i1]
                foundMatch = True
                break

        if not foundMatch:
            mergedColors.append(color)
            mergedCounts.append(counts[i1])

    return mergedColors, mergedCounts


def nearlyEqual(arr1, arr2):
    diff = 0
    r = min(len(arr1), len(arr2))
    for i in range(0, r):
        diff += abs(arr1[i] - arr2[i])

    return diff < 5


def getAllColors(filename, noBlackWhite=False):
    (colors, counts) = getColorCounts(filename)

    orderedColors1 = []
    orderedCounts1 = []

    while len(colors) > 0:
        index_max = numpy.argmax(counts)
        count = counts[index_max]

        mostColor = colors[index_max]

        acceptable = isColorAcceptable(mostColor, noBlackWhite)
        colorHex = arrayToHex(mostColor)
        log.debug(f"Color #{colorHex} Acceptable? {acceptable}")

        if acceptable:
            orderedColors1.append(mostColor)
            orderedCounts1.append(count)
        else:
            log.debug('Skipping and getting next...')

        counts = np.delete(counts, index_max)
        colors = np.delete(colors, index_max, axis=0)

    mergeSimilar(orderedColors1, orderedCounts1)

    orderedColors = []
    orderedCounts = []
    totalCount = 0

    while len(orderedColors1) > 0:
        index_max = numpy.argmax(orderedCounts1)
        count = orderedCounts1[index_max]
        totalCount += count

        mostColor = orderedColors1[index_max]
        colorHex = arrayToHex(mostColor)

        orderedColors.append(colorHex)
        orderedCounts.append(count)

        orderedCounts1 = np.delete(orderedCounts1, index_max)
        orderedColors1 = np.delete(orderedColors1, index_max, axis=0)

    percents = []
    finalColors = []

    log.debug("Ordered Colors:")
    for i in range(len(orderedColors)):
        pct = int((orderedCounts[i] / totalCount) * 100)
        percents.append(pct)
        log.debug(f"#{orderedColors[i]} - {pct}%")
        if pct > 2:
            finalColors.append(orderedColors[i])

    return finalColors, percents


def getDominantColor(filename, noBlackWhite=False):
    log.debug(f"Finding dominant color for {filename}")
    if noBlackWhite: log.debug("Ignoring Black and White")

    (colors, counts) = getColorCounts(filename)

    colorsFound = 0

    while (colorsFound < 1):  # TODO handle case where ALL are 'bad'?
        index_max = numpy.argmax(counts)  # find most frequent
        bestColor = colors[index_max]

        acceptable = isColorAcceptable(bestColor, noBlackWhite)

        colorHex = arrayToHex(bestColor)
        log.debug(f"Color #{bestColor} Acceptable? {acceptable}")

        if acceptable:
            colorsFound += 1
        else:
            log.debug('Removing and getting next...')
            counts = np.delete(counts, index_max)
            colors = np.delete(colors, index_max, axis=0)

    colorHex = arrayToHex(bestColor)

    log.debug(f"Most frequent acceptable color is #{colorHex}")
    return colorHex
