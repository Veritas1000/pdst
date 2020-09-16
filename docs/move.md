# `move` - Moving media files

Requires a setup configuration (see [the configuration documentation](readme.md) for more)

```
Usage: pdst move [OPTIONS] PATH...

Options:
  --skip-ext TEXT           When moving files, skip ones with this extension.
                            Can be passed multiple times to skip more than one
                            extension.
  --target-root PATH        Root of the library to move to. If not passed,
                            pulls from config entry 'moveTarget'.
  -m, --mode [video|image]  Operation mode (type of files to process)
  -o, --out PATH            Sets the output directory for created files
  -f, --force               Process files that would otherwise be skipped
  -R, --recurse             Recursively traverse directories
  -c, --config PATH         Specify a configuration JSON file
  -v, --verbose             Sets verbosity level
  --help                    Show this message and exit.
```

## Basic Usage

The `move` command provides a simple way to move and rename associated media files to a configured target library.

When passed a filename, it will move the file and any associated Plex files (e.g. files that have the same base 
name but different extensions) to target Plex library, potentially changing the show, timestamp, and title depending 
on how the matching sport entry in the config is setup.

### `--skip-ext TEXT` 

Skip specific extensions when moving files

### `--target-root PATH`

Root of the library to move to. If not passed, uses the config entry 'moveTarget'.

## Unused options

Even though they are listed as options (due to them being common options used in several other commands) Some options 
listed in `--help` aren't really used in `move`:

* `-m, --mode`
* `-o, --out`
* `-f, --force`