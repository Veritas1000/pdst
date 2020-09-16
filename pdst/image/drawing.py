import logging
from math import radians, cos, sin

from PIL import Image, ImageFilter, ImageChops, ImageColor

from pdst.image.spec import StrokeSpec, LayerGroupSpec, LayerSpec
from pdst.image.util import withAlpha, transparentCopy, paste2

log = logging.getLogger(__name__)


def drawStroke(baseImage, strokeSpec, drawPoint, maskImg):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    if maskImg.mode in ['RGBA', 'L']:
        pasteMask = maskImg
    else:
        pasteMask = None

    strokeColor = strokeSpec.color
    strokeBase = Image.new('RGBA', baseImage.size, withAlpha(strokeColor, 0))
    strokeImg = Image.new('RGBA', maskImg.size, strokeColor)
    strokeSize = strokeSpec.size

    offsets = []
    # Circle method
    steps = 8 * strokeSize
    for ds in range(0, steps):
        rad = radians(ds * (360 / steps))
        dx = strokeSize * cos(rad)
        dy = strokeSize * sin(rad)
        point = (round(drawPoint[0] + dx), round(drawPoint[1] + dy))
        offsets.append(point)

    for position in offsets:
        strokeBase.paste(strokeImg, position, pasteMask)

    strokeTransparent = Image.new('RGBA', baseImage.size, withAlpha(strokeColor, 0))
    strokeAlpha = Image.blend(strokeTransparent, strokeBase, strokeSpec.opacity)
    baseImage = Image.alpha_composite(baseImage, strokeAlpha)
    return baseImage


def dropShadow(baseImage, shadowSpec, drawPoint, maskImg):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    if maskImg.mode in ['RGBA', 'L']:
        shadowImgMode = 'RGBA'
        pasteMask = maskImg
    else:
        shadowImgMode = 'RGB'
        pasteMask = None

    shadowColor = (0, 0, 0)
    shadowA = round(shadowSpec.opacity * 255)
    shadow = Image.new(shadowImgMode, maskImg.size, withAlpha(shadowColor, shadowA))

    radAngle = radians(shadowSpec.angleDeg)
    offsetX = round(cos(radAngle) * shadowSpec.offset) + drawPoint[0]
    offsetY = round(sin(radAngle) * shadowSpec.offset) + drawPoint[1]

    shadowImage = transparentCopy(baseImage)
    shadowImage.paste(shadow, (offsetX, offsetY), pasteMask)
    shadowBlur = shadowImage.filter(ImageFilter.GaussianBlur(shadowSpec.spread))

    out = Image.alpha_composite(baseImage, shadowBlur)
    return out


def outerGlow(baseImage, outerGlowSpec, drawPoint, maskImg):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    if maskImg.mode in ['RGBA', 'L']:
        imgMode = 'RGBA'
    else:
        imgMode = 'RGB'

    glowColor = ImageColor.getrgb(f"#{outerGlowSpec.colorHex}")
    glowImage = Image.new(imgMode, baseImage.size, withAlpha(glowColor, 0))

    strokeSpec = StrokeSpec(round(outerGlowSpec.spread * 0.9),
                            colorHex=outerGlowSpec.colorHex,
                            opacity=outerGlowSpec.opacity)
    glowImage = drawStroke(glowImage, strokeSpec, drawPoint, maskImg)

    glowBlurred = glowImage.filter(ImageFilter.GaussianBlur(outerGlowSpec.spread))

    out = Image.alpha_composite(baseImage, glowBlurred)
    return out


def colorOverlay(baseImage, maskSpec, drawPoint, maskImg):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    maskColor = maskSpec.color

    maskBase = Image.new('RGBA', baseImage.size, withAlpha(maskColor, 0))
    maskImage = Image.new('RGBA', maskImg.size, maskColor)
    maskBase.paste(maskImage, drawPoint, maskImg)

    maskTransparent = Image.new('RGBA', baseImage.size, withAlpha(maskColor, 0))
    maskAlphaAlpha = Image.blend(maskTransparent, maskBase, maskSpec.opacity)

    out = Image.alpha_composite(baseImage, maskAlphaAlpha)
    return out


def drawLayerSpec(baseImage, layerSpec):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    layerBase = transparentCopy(baseImage)
    layerEffects = layerSpec.effects
    drawPoint = layerSpec.offset
    layerImg = layerSpec.image

    if layerEffects.dropShadow is not None:
        layerBase = dropShadow(layerBase, layerEffects.dropShadow, drawPoint, layerImg)

    if layerEffects.outerGlow is not None:
        layerBase = outerGlow(layerBase, layerEffects.outerGlow, drawPoint, layerImg)

    if layerEffects.stroke is not None:
        layerBase = drawStroke(layerBase, layerEffects.stroke, drawPoint, layerImg)

    layerBase = paste2(layerBase, layerImg, drawPoint)

    if layerEffects.colorOverlay is not None:
        layerBase = colorOverlay(layerBase, layerEffects.colorOverlay, drawPoint, layerImg)

    if layerSpec.alphaMask is not None:
        fullMask = Image.new('L', baseImage.size, 0)
        fullMask.paste(layerSpec.alphaMask, drawPoint)
        layerBase.putalpha(fullMask)

    outImage = Image.alpha_composite(baseImage, layerBase)
    return outImage


def drawLayers(baseImage, layerSpecs):
    if baseImage.mode != 'RGBA':
        baseImage = baseImage.convert('RGBA')

    outImg = baseImage
    for layer in layerSpecs:
        if isinstance(layer, LayerGroupSpec):
            outImg = drawLayerGroup(outImg, layer)
        else:
            outImg = drawLayerSpec(outImg, layer)

    return outImg


def drawLayerGroup(baseImage, layerGroup):
    layerBase = transparentCopy(baseImage)

    groupImg = drawLayers(layerBase, layerGroup.memberLayers)

    groupLayerSpec = LayerSpec(groupImg,
                               layerGroup.offset,
                               layerGroup.effects,
                               layerGroup.alphaMask)

    outImg = drawLayerSpec(baseImage, groupLayerSpec)

    return outImg
