import os
import pathlib

import click

from pdst import parsing, analysis
from pdst.image import ImageGenerationException
from pdst.cli import pass_environment, common_options, OpMode
from pdst.commands import helpers
from pdst.image.spec import ImageSpec, ColorOverlaySpec, StrokeSpec, CompositeSpec


def shouldProcessFile(ctx, path):
    process = False
    if os.path.isfile(path):
        if ctx.mode is OpMode.VIDEO:
            (root, ext) = os.path.splitext(path)
            ext = ext[1:]
            hasImage = False
            if ext in ctx.config.videoExtensions:
                for imageExt in ctx.config.imageExtensions:
                    imageFile = root + '.' + imageExt
                    if os.path.exists(imageFile):
                        hasImage = True

                process = ctx.force or not hasImage
        else:
            validImage = analysis.isValidImage(path)
            # colorInName = parsing.hasTrailingColorInName(path)
            process = validImage  # and (ctx.force or not colorInName)

    if not process:
        ctx.vlog(f"Not processing {path}")

    return process


def processSingleFile(ctx, inFile):
    if ctx.mode is OpMode.VIDEO:
        processVideoFile(ctx, inFile)
    else:
        processImageFile(ctx, inFile)


def processVideoFile(ctx, inFile):
    ctx.vlog(f"Processing video file: {os.path.basename(inFile)}")

    try:
        thumb = ctx.imageService.generateEventThumbnail(inFile)
        imageName = ctx.imageService.getMatchingImageName(inFile)
        (originalDir, imageFile) = os.path.split(imageName)

        if ctx.outDir is not None:
            imageName = os.path.join(ctx.outDir, imageFile)

        ctx.log(f"Saving {imageFile}")
        thumb.save(imageName)
    except ImageGenerationException as e:
        ctx.log(f"There was a problem generating the image: {e}")


def processImageFile(ctx, inFile):
    ctx.vlog(f"Processing image file: {os.path.basename(inFile)}")

    colorInName = parsing.hasHints(inFile)
    detectColors = ctx.force or not colorInName

    # need to figure out how the trial/error workflow will work with the new
    # ImageGenerator and backgrounds and stuff
    if ctx.allColors and detectColors:  # pragma: no cover
        (orderedColors, percents) = analysis.getAllColors(inFile)

        # use existing color from filename if present in case it *isn't* in logo
        if colorInName:
            generateAndSaveLogoImage(ctx, inFile, None)

        if len(orderedColors) == 1:
            generateAndSaveLogoImage(ctx, inFile, 'eee')
            generateAndSaveLogoImage(ctx, inFile, orderedColors[0], True)
        else:
            for i, color in enumerate(orderedColors):
                generateAndSaveLogoImage(ctx, inFile, color, index=i)
    else:
        generateAndSaveLogoImage(ctx, inFile, None)


def generateAndSaveLogoImage(ctx, logoFile, color, invert=False, index=None):
    imageSize = ctx.imageSize
    if color is None:
        imageSpec = ImageSpec(logoFile)
        override = getImageSpecOverride(ctx)
        imageSpec.override(override)
    else:
        imageSpec = ImageSpec(logoFile, colors=[color], invert=invert, bg='solid')

    compSpec = CompositeSpec(imageSize, ctx.text)
    teamImg = ctx.imageGenerator.generateImage(compSpec, [imageSpec])

    imageFile = os.path.split(logoFile)[1]
    nameBase = parsing.cleanImageHints(imageFile)
    if color is None:
        imageName = os.path.splitext(imageFile)[0]
    else:
        imageName = nameBase
        if index is not None:
            imageName += f'_[{index}]'

        imageName += f'_{color}'
        if invert:
            imageName += 'i'

    imageName += '.' + ctx.config.createdImageExtension
    saveImage(ctx, teamImg, imageName)


def saveImage(ctx, image, imageName):
    if ctx.outDir is not None:
        finalPath = os.path.join(ctx.outDir, imageName)
    else:
        finalPath = os.path.join(os.getcwd(), imageName)

    ctx.log(f"Saving {finalPath}")
    image.save(finalPath)


def processTeamsSpecs(ctx, teamSpecs):
    basename = ' vs. '.join([s.teamName for s in teamSpecs if s is not None])
    ctx.log(f"Generating image for {basename}")
    override = getImageSpecOverride(ctx)
    img = ctx.imageService.generateImage(ctx.imageSize, teamSpecs, override, text=ctx.text)

    filename = f"{basename}.{ctx.config.createdImageExtension}"
    if ctx.outDir is None:
        ctx.outDir = os.getcwd()

    fullOutPath = os.path.join(ctx.outDir, filename)
    img.save(fullOutPath)


def getImageSpecOverride(ctx):
    override = ImageSpec(None)
    if len(ctx.colors) > 0:
        override.colors = ctx.colors

    override.bg = ctx.background
    override.invert = ctx.invert

    if ctx.colorOverlay is not None:
        override.maskSpec = ColorOverlaySpec(ctx.colorOverlay)

    if ctx.stroke[0] is not None:
        override.strokeSpec = StrokeSpec(ctx.stroke[0], ctx.stroke[1])

    return override


class PathOrSpecifier(click.ParamType):
    def __init__(self):
        self.path = click.Path(exists=True)

    def convert(self, value, param, ctx):
        if parsing.isTeamsString(value):
            return parsing.parseTeamsString(value)
        else:
            clickPathValue = self.path.convert(value, param, ctx)
            formatted = click.format_filename(clickPathValue)
            return pathlib.Path(formatted)


@click.command("generate", short_help="Image generation tools")
@click.option("-a", "--all-colors", is_flag=True, help="Generate separate images using all colors "
                                                       "found by analyzing the given image(s). "
                                                       "Implies --mode=IMAGE.")
@click.option("--color", multiple=True, help="Generate an image using the given color. "
                                             "Can be passed multiple times to set more than one color "
                                             "(e.g for backgrounds that support multiple colors). "
                                             "Implies --mode=IMAGE")
@click.option("--invert", "inversion", flag_value="True", help="Explicitly enable logo invert mode")
@click.option("--no-invert", "inversion", flag_value="False", help="Explicitly disable logo invert mode")
@click.option("--background", "--bg", help="Set/override the background setting")
@click.option("-s", "--size", type=int, nargs=2, help="Set the generated image size (width height)")
@click.option("--mask", help="Draw the logo as a mask of the given color (hex)")
@click.option("--stroke", type=(int, str), default=(None, None),
              help="Draw a stroke of the given size and color around the logo")
@click.option("--text", help="Overlay the given text onto the image")
@click.argument("source", required=False, type=PathOrSpecifier(), nargs=-1)
@common_options
@pass_environment
def cli(ctx, all_colors, color, inversion, background, size, mask, stroke, text, source):
    ctx.allColors = all_colors
    ctx.force = ctx.force or all_colors
    ctx.colors = [c for c in color]
    ctx.invert = inversion == 'True' if inversion is not None else None
    ctx.background = background
    ctx.colorOverlay = mask
    ctx.stroke = stroke
    ctx.text = text

    if all_colors or color or inversion or background or mask or stroke[0] or text:
        ctx.mode = OpMode.IMAGE

    if len(size) != 2:
        ctx.imageSize = ctx.config.thumbnailSize
    else:
        ctx.imageSize = size

    for s in source:
        if isinstance(s, pathlib.Path):
            p = str(s)
            helpers.handlePath(ctx, p, checkFile=shouldProcessFile, handleFile=processSingleFile)
        else:
            processTeamsSpecs(ctx, s)
