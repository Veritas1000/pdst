import numpy
from PIL import Image


def verifyImagesEquivalent(expectedImagePath, compareImagePath, threshold):
    expectedImage = Image.open(expectedImagePath)
    compareImage = Image.open(compareImagePath)

    if expectedImage.size != compareImage.size:
        return False, f'Image sizes do not match! {expectedImage.size} != {compareImage.size}'

    exp = numpy.asarray(expectedImage)
    comp = numpy.asarray(compareImage)
    expectedImage.close()
    compareImage.close()

    err = numpy.sum((exp - comp) ** 2)
    err /= float(exp.shape[0] * exp.shape[1])

    if err > threshold:
        return False, f"Images do not match: error = {err}"
    else:
        return True, f"Images close enough, error = {err}"
