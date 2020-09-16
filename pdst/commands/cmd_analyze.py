import os

import click
from PIL import ImageColor

from pdst import parsing, analysis
from pdst.image.ImageMatcher import ImageMatcher
from pdst.cli import pass_environment, common_options, OpMode
from pdst.commands import helpers


def shouldProcessFile(ctx, path):
    shouldProcess = False
    if ctx.mode is OpMode.VIDEO and helpers.isVideoFile(ctx, path):
        hasImg = hasImage(ctx, path)
        shouldProcess = ctx.force or not hasImg

    elif ctx.mode is OpMode.IMAGE and analysis.isValidImage(path):
        colorInName = parsing.hasHints(path)
        shouldProcess = ctx.force or not colorInName

    if not shouldProcess:
        ctx.vlog(f"Not processing {path}")

    return shouldProcess


def hasImage(ctx, path):
    hasImg = False
    root = os.path.splitext(path)[0]
    for imageExt in ctx.config.imageExtensions:
        imageFile = root + '.' + imageExt
        if os.path.exists(imageFile):
            hasImg = True

    return hasImg


def analyzeSingleFile(ctx, filePath):
    ctx.vlog(f"Analyzing {filePath}")
    if ctx.mode is OpMode.IMAGE:
        analyzeImage(ctx, filePath)
    elif ctx.mode is OpMode.VIDEO:
        analyzeVideo(ctx, filePath)


def analyzeVideo(ctx, videoPath):
    (dirname, filename) = os.path.split(os.path.abspath(videoPath))
    (team1, team2) = parsing.teamNamesFromFilename(filename)

    dirParts = dirname.split(os.sep)
    parentDir = dirParts[-1]
    grandparentDir = dirParts[-2]

    sportEntry = ctx.sportService.getSportFor(videoPath)

    # TODO: Handle only *one* team found in filename

    if team1 is None and team2 is None:
        ctx.log(f"---- {filename} ----")
        ctx.log(f"{sportEntry.name}: {sportEntry.getDefaultImage()}")
    else:
        m = ImageMatcher(sportEntry.imageRoot)
        (logo1, logo2) = m.findBestMatches(team1, team2, parentDir, grandparentDir)

        ctx.log(f"---- {filename} ----")
        ctx.log(f"{sportEntry.name}/{team1}: {logo1}")
        ctx.log(f"{sportEntry.name}/{team2}: {logo2}")


def analyzeImage(ctx, imageFile):
    invert = False

    if ctx.allColors:
        (orderedColors, percents) = analysis.getAllColors(imageFile, ctx.noBW)

        ctx.log(f"Colors in {imageFile} from most to least common:")
        for i in range(len(orderedColors)):
            ctx.log(f"[{i}] #{orderedColors[i]} - {percents[i]}%")

        color = orderedColors[0]

        if ctx.interactive:  # pragma: no cover
            askInvert = len(orderedColors) == 1

            if askInvert:
                choice = input('There is only one color in the logo. Do you want to want to use inverted mode? [y/N]: ')

                if choice is not None:
                    invert = choice.startswith(('y', 'Y'))

            else:
                choice = input('Enter the number of the color you wish to choose [0]: ')

                if choice is not None and len(choice) > 0:
                    ctx.vlog(f"#{choice}")
                    try:
                        num = int(choice)
                        color = orderedColors[num]
                    except:
                        try:  # ability to specify *any* hex code in interactive mode :)
                            temp = ImageColor.getrgb(f"#{choice}")
                            color = choice
                        except:
                            ctx.log(
                                f"Unknown selection: {choice}, falling back to most common color #{orderedColors[0]}")
                            color = orderedColors[0]

    else:
        color = analysis.getDominantColor(imageFile, ctx.noBW)
        ctx.log(f"The most common color in {imageFile} is #{color}")

    if ctx.tint:  # pragma: no cover
        ctx.vlog(f"Tinting {int(ctx.tint * 100)}%")
        original = ImageColor.getrgb("#" + color)

        newR = original[0] + ((255 - original[0]) * ctx.tint)
        newG = original[1] + ((255 - original[1]) * ctx.tint)
        newB = original[2] + ((255 - original[2]) * ctx.tint)

        newColor = analysis.arrayToHex([newR, newG, newB])
        ctx.log(f"Tinted #{color} to #{newColor}")
        color = newColor

    # TODO: how to handle color = None at this point? is that really even possible outside bad images?
    if ctx.rename:
        newFileName = parsing.setColorInFilename(imageFile, color, invert)
        os.rename(imageFile, newFileName)  # TODO: use os.replace() instead?
        ctx.log(f"{imageFile} -> {newFileName}")


@click.command("analyze", short_help="Analysis utilities")
@click.argument("path", required=True, type=click.Path(exists=True), nargs=-1)
@click.option("--no-black-white", is_flag=True,
              help="When analyzing image colors, ignore colors very close to black/white")
@click.option("-a", "--all-colors", is_flag=True,
              help="Show all colors found in the image, in order from most common to least")
@click.option("-r", "--rename", is_flag=True, help="Rename logo filenames to include the color code")
@click.option("-i", "--interactive", is_flag=True,
              help="Interactively choose the color to write when using the '--rewrite' option. "
                   "Implies '--all-colors' and '--rename'")
@click.option("-t", "--tint", type=float, help="Tint analyzed colors to X% white value. should be (0.0-1.0)")
@common_options
@pass_environment
def cli(ctx, path, no_black_white, all_colors, rename, interactive, tint):
    # ctx.force = True
    ctx.noBW = no_black_white
    ctx.allColors = all_colors or interactive
    ctx.rename = rename or interactive
    ctx.interactive = interactive
    ctx.tint = tint

    if rename or interactive or all_colors or no_black_white or tint:
        ctx.mode = OpMode.IMAGE
        ctx.outDir = os.getcwd()

    for p in path:
        # fmtPath = os.path.abspath(click.format_filename(p))
        fmtPath = click.format_filename(p)
        helpers.handlePath(ctx, fmtPath, checkFile=shouldProcessFile, handleFile=analyzeSingleFile)
