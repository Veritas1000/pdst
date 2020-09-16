from PIL import ImageColor

from pdst import parsing


class ImageSpec:

    def __init__(self, imageFile, isLogo=True, colors=None, bg=None, invert=None, strokeSpec=None, maskSpec=None):
        self.imageFile = imageFile
        self.isLogo = isLogo

        # TODO: move the filename parsing logic from LogoDrawCfg to here
        self.colors = colors
        self.bg = bg
        self.invert = invert

        self.strokeSpec = strokeSpec

        if maskSpec is None and imageFile is not None:
            maskHint = parsing.getMaskHint(imageFile)
            if maskHint is not None:
                maskSpec = ColorOverlaySpec(maskHint)

        self.maskSpec = maskSpec

    def override(self, other):
        if other.colors is not None:
            self.colors = other.colors
        if other.bg is not None:
            self.bg = other.bg
        if other.invert is not None:
            self.invert = other.invert
        if other.strokeSpec is not None:
            self.strokeSpec = other.strokeSpec
        if other.maskSpec is not None:
            self.maskSpec = other.maskSpec

    def __eq__(self, other):
        if isinstance(other, ImageSpec):
            return self.imageFile == other.imageFile \
                   and self.isLogo == other.isLogo

        return False

    def __str__(self):
        if self.isLogo:
            return f"Logo: {self.imageFile}"
        else:
            return f"Non-Logo: {self.imageFile}"

    def __repr__(self):
        return self.__str__()


class CompositeSpec:
    def __init__(self, size, text=None):
        self.size = size
        self.text = text


class StrokeSpec:

    def __init__(self, size=2, colorHex=None, opacity=1.0, color=None):
        self.size = size
        self.colorHex = colorHex
        self.color = color
        self.opacity = opacity

        if self.color is None:
            self.color = ImageColor.getrgb(f"#{self.colorHex}")


class ColorOverlaySpec:

    def __init__(self, colorHex=None, opacity=1.0, color=None):
        self.colorHex = colorHex
        self.opacity = opacity

        self.color = color
        if self.color is None:
            self.color = ImageColor.getrgb(f"#{self.colorHex}")


class DropShadowSpec:
    def __init__(self, spread, offset, angleDeg=0, opacity=0.7):
        self.spread = spread
        self.offset = offset
        self.angleDeg = angleDeg
        self.opacity = opacity


class OuterGlowSpec:
    def __init__(self, spread, colorHex, opacity=1.0):
        self.spread = spread
        self.colorHex = colorHex
        self.opacity = opacity


class LayerEffects:
    def __init__(self, stroke=None, colorOverlay=None, dropShadow=None, outerGlow=None):
        self.stroke = stroke
        self.colorOverlay = colorOverlay
        self.dropShadow = dropShadow
        self.outerGlow = outerGlow


class LayerSpec:
    def __init__(self, layerImage, drawOffset=(0, 0), layerEffects=LayerEffects(), alphaMask=None):
        self.image = layerImage
        self.offset = drawOffset
        self.effects = layerEffects
        self.alphaMask = alphaMask


class LayerGroupSpec:
    def __init__(self, memberLayers, drawOffset=(0, 0), layerEffects=LayerEffects(), alphaMask=None):
        self.memberLayers = memberLayers
        self.offset = drawOffset
        self.effects = layerEffects
        self.alphaMask = alphaMask
