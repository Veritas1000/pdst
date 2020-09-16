# `clean` - Cleanup files

Cleanup orphaned files or old episodes.

```
Usage: pdst clean [OPTIONS] PATH...

Options:
  --older TEXT              Only clean files older than the given age. Implies
                            '--force'
  -m, --mode [video|image]  Operation mode (type of files to process)
  -o, --out PATH            Sets the output directory for created files
  -f, --force               Process files that would otherwise be skipped
  -R, --recurse             Recursively traverse directories
  -c, --config PATH         Specify a configuration JSON file
  -v, --verbose             Sets verbosity level
  --help                    Show this message and exit.
```

## Basic Usage

By default, `clean` looks for files in the given path that do not have an associated video file and deletes them. This
can be used to keep old generated thumbnails and metadata from bloating your dvr or sports library since when deleting
an episode from within Plex, the thumbnail and metadata files are not deleted - just the video file.

### `--older TEXT`

Only clean files older than the given age. Expects and argument that specifies a time span in hours, days, or weeks. 

Examples:

* `--older 1w` - older than 1 week
* `--older 2d` - older than 2 days
* `--older 7w3d2h` - older than 7 weeks, 3 days, and 2 hours
* `--older '7w 2d 2h 1d'` - same as above. The specifier can be any combination of possibly multiple '\<number\>[w|d|h]', 
and the values will simply be added together (2d + 1d = 3d)

## Unused options

Even though they are listed as options (due to them being common options used in several other commands) Some options 
listed in `--help` aren't really used in `clean`:

* `-m, --mode`
* `-o, --out`