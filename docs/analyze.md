# `analyze` - Image and Filename Analysis

```
Usage: pdst analyze [OPTIONS] PATH...

Options:
  --no-black-white          When analyzing image colors, ignore colors very
                            close to black/white
  -a, --all-colors          Show all colors found in the image, in order from
                            most common to least
  -r, --rename              Rename logo filenames to include the color code
  -i, --interactive         Interactively choose the color to write when using
                            the '--rewrite' option. Implies '--all-colors' and
                            '--rename'
  -t, --tint FLOAT          Tint analyzed colors to X% white value. should be
                            (0.0-1.0)
  -m, --mode [video|image]  Operation mode (type of files to process)
  -o, --out PATH            Sets the output directory for created files
  -f, --force               Process files that would otherwise be skipped
  -R, --recurse             Recursively traverse directories
  -c, --config PATH         Specify a configuration JSON file
  -v, --verbose             Sets verbosity level
  --help                    Show this message and exit.
```

## Basic Usage

### Analyze a video file

You can use `pdst analyze` to check your configuration and logo organization without having to 
generate test images.

The given filename will be parsed for a sport and team names, and logos will be found for those 
team names. `analyze` will print the sport and team names pulled from the filename, as well as 
the logo image that would be used to generate an image.

Obviously, doing this requires a setup configuration and logos (see [the configuration 
documentation](readme.md) for more). This example assumes a setup config similar to the 
test config setup in the [generate Basic Usage section](generate.md#basic-usage)

Example:
```
pdst analyze test-files/testMedia/Sport\ Alpha\ \(2009\)/Season\ 2020/Sport\ Alpha\ \(2009\)\ -\ 2020-08-03\ 08\ 00\ 00\ -\ Team\ Alpha\ vs.\ Team\ Bravo.ts
```
outputs:
```
---- Sport Alpha (2009) - 2020-08-03 08 00 00 - Team Alpha vs. Team Bravo.ts ----
Sport Alpha/Team Alpha: test-files/logos/plain/Alpha.png
Sport Alpha/Team Bravo: test-files/logos/plain/Bravo.png
```

### See 'all' colors in an image

By passing `analyze` an image file along with the `-a`/`--all-colors` flag, the image will be 
analyzed, and the colors found will be printed to the console in order from most to least common.

Note that any color that occurs in less than 2% of the image will not be shown.

```
pdst analyze -a test-files/logos/plain/Bravo.png
```
```
Colors in test-files/logos/plain/Bravo.png from most to least common:
[0] #031734 - 23%
[1] #e7dcca - 11%
[2] #036463 - 10%
[3] #cbb280 - 4%
```