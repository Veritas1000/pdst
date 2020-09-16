import logging
from math import sqrt

from PIL import Image

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
