import os
import shutil

import click

import pdst.commands.helpers as helpers
from pdst import filetools
from pdst.cli import pass_environment, common_options


def moveAssociatedFiles(ctx, videoPath):
    ctx.vlog(f"Moving {videoPath} and associated files...")
    metadata = ctx.metadataService.getMetadataForEpisodeFile(videoPath)

    if metadata is None:
        ctx.log(f"NO metadata found for {videoPath}! Not Moving", err=True)
        return

    # Should already be set when Config was loaded, but make sure since we might be
    # about to create a bunch of dirs/files
    os.umask(ctx.config.umask)

    newRootPath = ctx.config.moveTarget
    newShowDirName = metadata.show.title
    newSeasonDirName = f"Season {metadata.season.index}"
    destinationDir = os.path.join(newRootPath, newShowDirName, newSeasonDirName)

    if not os.path.exists(destinationDir):
        ctx.vlog(f"Creating destination directories: {destinationDir}")
        os.makedirs(destinationDir)

    showPosterFile = os.path.join(newRootPath, newShowDirName, 'poster.jpg')
    if not os.path.exists(showPosterFile):
        ctx.vlog(f"Destination show does not have an existing poster")
        existingThumb = os.path.join(ctx.config.plexLibPath, filetools.getRealThumbPath(metadata.show))
        if os.path.exists(existingThumb):
            ctx.vlog(f"Copying 'old' library show poster: {existingThumb}")
            shutil.copy(existingThumb, showPosterFile)
        else:
            ctx.vlog(f"{existingThumb} doesn't seem to exist?")

    renamed = filetools.getMoveDestinationFilename(videoPath, metadata, destinationDir)
    for filePath in filetools.getPlexAssociatedFiles(videoPath):
        thisExt = os.path.splitext(filePath)[1]
        if thisExt[1:] not in ctx.skipExt:
            newPath = os.path.join(destinationDir, renamed + thisExt)
            os.rename(filePath, newPath)
            ctx.vlog(f"{filePath} -> {newPath}")
        else:
            ctx.vlog(f"Skipping {filePath}")


@click.command("move", short_help="Move media")
@click.option("--skip-ext", multiple=True, help="When moving files, skip ones with this extension. "
                                                "Can be passed multiple times to skip more than one "
                                                "extension.")
@click.option("--target-root", type=click.Path(exists=True), help="Root of the library to move to. "
                                                                  "If not passed, pulls from config "
                                                                  "entry 'moveTarget'.")
@click.argument("path", required=True, nargs=-1)
@common_options
@pass_environment
def cli(ctx, skip_ext, target_root, path):
    ctx.skipExt = skip_ext

    if target_root is not None:
        ctx.config.moveTarget = target_root

    for p in path:
        fmtPath = os.path.abspath(click.format_filename(p))
        helpers.handlePath(ctx, fmtPath, checkFile=helpers.isVideoFile, handleFile=moveAssociatedFiles)
