import os


def basicCheckFile(ctx, filePath):
    return os.path.isfile(filePath)


def isVideoFile(ctx, filePath):
    isVideo = False
    if os.path.isfile(filePath):
        (root, ext) = os.path.splitext(filePath)
        ext = ext[1:]
        isVideo = ext in ctx.config.videoExtensions

    return isVideo


def basicHandleFile(ctx, filePath):
    ctx.log(f"Default no-op file handler: {filePath}")


def basicHandleDir(ctx, path, handleDir=None, checkFile=basicCheckFile, handleFile=basicHandleFile):
    if handleDir is None:
        handleDir = basicHandleDir

    ctx.vlog(f"Processing directory: {path}")
    for f in os.scandir(path):
        if ctx.recurse and os.path.isdir(f.path):
            handlePath(ctx, f.path, handleDir=handleDir, checkFile=checkFile, handleFile=handleFile)
        elif checkFile(ctx, f.path):
            handleFile(ctx, f.path)


def handlePath(ctx, path, handleDir=basicHandleDir, checkFile=basicCheckFile, handleFile=basicHandleFile):
    if os.path.isdir(path):
        handleDir(ctx, path, handleDir=handleDir, checkFile=checkFile, handleFile=handleFile)
    elif checkFile(ctx, path):
        handleFile(ctx, path)


def isPosterImage(path):
    basename = os.path.split(path)[1]
    return os.path.splitext(basename)[0].lower() in ['folder', 'poster', 'show']
