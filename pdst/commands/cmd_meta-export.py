import os

import click

import pdst.commands.helpers as helpers
from pdst.cli import pass_environment, common_options
from pdst.filetools import getMetadataFilename


def shouldProcess(ctx, filePath):
    process = False
    if os.path.isfile(filePath):
        (root, ext) = os.path.splitext(filePath)
        ext = ext[1:]
        if ext in ctx.config.videoExtensions:
            metadataPath = getMetadataFilename(filePath)
            ctx.vlog(f"Has metadata file?: {filePath} : ", nl=False)

            hasMetadata = False
            if os.path.exists(metadataPath):
                hasMetadata = True

            ctx.vlog(f"{hasMetadata}")

            process = ctx.force or not hasMetadata

    if not process:
        ctx.vlog(f"not processing {filePath}")

    return process


def processFile(ctx, filePath):
    ctx.vlog(f"Processing {filePath}")

    metadata = ctx.metadataService.getMetadataForEpisodeFile(filePath, readFromFile=False)

    if metadata is None:
        ctx.log(f"NO metadata found in db for {filePath}!", err=True)
        return

    ctx.vlog(f"{filePath} => {metadata}")

    fileName = getMetadataFilename(filePath)
    metadata.writeToFile(fileName)


@click.command("meta-export", short_help="Plex Metadata Export")
@click.argument("path", required=True, nargs=-1)
@common_options
@pass_environment
def cli(ctx, path):
    for p in path:
        fmtPath = os.path.abspath(click.format_filename(p))
        helpers.handlePath(ctx, fmtPath, checkFile=shouldProcess, handleFile=processFile)
