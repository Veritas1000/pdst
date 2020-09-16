# pdst CLI
```
Usage: pdst [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  analyze      Analysis utilities
  clean        Cleanup orhpaned files
  generate     Image generation tools
  meta-export  Plex Metadata Export
  move         Move media
```

# Common/Shared command options

There are several options that can be used with any of the `pdst` commands, though depending on 
the particular command, the behavior of the option may change slightly.

## `-m, --mode [video|image]`
 
One of `video` or `image`

Sets the operation mode. Defaults to `video`, 
though in some cases other options will auto-set the mode to `image` (indicated by the option stating that it 
`Implies --mode image`)
 
## `-o, --out PATH`

Sets the output directory for created files. 

The default depends on the operation mode. In `video` mode, the default is 
to generate the images alongside the video file. In `image` mode the default is to use the current directory.

## `-f, --force`

Process files that would otherwise be skipped. 

In `video` mode, a video file would be skipped if it already has a 
thumbnail file (an image with the same base filename)

In `image` mode, a file would generally be skipped if it already has [hints](generate.md#image-generation-filename-hinting) in the filename

## `-R, --recurse`

Recursively traverse directories under a given path. 

Otherwise only files in that directory will be checked/processed.

## `-c, --config PATH`

Specify a [configuration](readme.md) JSON file. 

Can also be set via an environment variable `PDST_CFG`

## `-v, --verbose`

Sets verbosity level. Can increase verbosity by passing more than one `v`, e.g. `-vv`