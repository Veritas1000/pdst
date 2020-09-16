import os
from datetime import datetime

import click

import pdst.commands.helpers as helpers
from pdst import filetools, parsing
from pdst.cli import pass_environment, common_options


def checkFile(ctx, filePath):
    isPoster = helpers.isPosterImage(filePath)

    hasMatchingVideo = False
    videoPath = None
    for path in filetools.getPlexAssociatedFiles(filePath):
        if helpers.isVideoFile(ctx, path):
            hasMatchingVideo = True
            videoPath = path
            break

    old = True
    if videoPath is not None:
        filetime = datetime.fromtimestamp(os.path.getmtime(videoPath))
        if filetime is not None and ctx.cutoffTime is not None:
            old = filetime < ctx.cutoffTime

    process = not isPoster and old and (ctx.force or not hasMatchingVideo)
    if not process:
        ctx.vlog(f"Skipping {filePath}")
    return process


def cleanAssociatedFiles(ctx, filePath):
    for path in filetools.getPlexAssociatedFiles(filePath):
        ctx.vlog(f"Deleting {path}")
        os.remove(path)


@click.command("clean", short_help="Cleanup orhpaned files")
# @click.option("--skip-ext", multiple=True, help="When moving files, skip ones with this extension. "
#                                                 "Can be passed multiple times to skip more than one "
#                                                 "extension.")
@click.option("--older",  help="Only clean files older than the given age. Implies '--force'")
@click.argument("path", required=True, nargs=-1)
@common_options
@pass_environment
def cli(ctx, older, path):

    ctx.cutoffTime = None
    delta = parsing.parseTimedelta(older)
    if delta is not None:
        ctx.force = True
        now = datetime.now()
        ctx.cutoffTime = now - delta

    for p in path:
        fmtPath = os.path.abspath(click.format_filename(p))
        helpers.handlePath(ctx, fmtPath, checkFile=checkFile, handleFile=cleanAssociatedFiles)
