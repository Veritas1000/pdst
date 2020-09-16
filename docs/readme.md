# Configuration

Many aspects of the behavior of `pdst` are configurable, and the best way to setup the configuration is through 
the use of a config `.json` file. See [`sample_config.json`](sample_config.json) for an example file you can modify for your particular setup.

Once setup, you can tell `pdst` to use your configuration by passing the `--config` option on the command line,
or by setting up an environment variable `PDST_CFG` pointing to the config file location

```json
{
    "sports": [
    {
        "name": "NCAA",
        "imageRoot": "/media/images/NCAA",
        "matches": ["NCAA Football", "College Football", "(NCAA|College) (Football|Basketball)"]
    },
    {
        "name": "International",
        "imageRoot": "/media/images/National.Flags",
        "dateOverride": "ALWAYS",
        "matches": [
            "World", "Olympics?", "(inter)?national",
            { "match": "UEFA Nations League", "overrideShow": "UEFA Nations League" }
        ],
        "background": "blurzoom"
    },
    {
        "name": "Premier League",
        "imageRoot": "/media/images/Soccer/UEFA/Premier.League",
        "logo": "/media/images/Soccer/Premier_League_logo.png"
    },
    {
        "name": "Soccer",
        "imageRoot": "/media/images/Soccer",
        "matches": ["Gold Cup", "CONCACAF", "Soccer"]
    },
    {
        "name": "NFL",
        "imageRoot": "/media/images/NFL"
    },
    {
        "name": "NBA",
        "imageRoot": "/media/images/NBA",
        "imageTextRegex": "(Game \\d+)"
    },
    {
        "name": "Formula 1",
        "image": "/media/images/Motorsport/Formula.1/f1_thumb.png",
        "imageRoot": "/media/images/Motorsport/Formula.1/",
        "matches": ["Formula (One|1)"]
    }
    ],
    "imageRoot": "/data/images",
    "thumbnailSize": [600, 340],
    "fallbackColor": "#111",
    "videoExtensions": ["mkv", "ts", "mp4"],
    "imageExtensions": ["png", "jpg", "jpeg"],
    "createdImageExtension": "png",
    "plexLibrary": "/data/config/Library/Application Support/Plex Media Server",
    "moveTarget": "/data/media/video/new-sports",
    "umask": "002"
}
```

## `sports`

The `sports` section is the most important for consistent behavior, as this is where the matching and lookup of 
sports and team names to logos is determined.

In the context of this tool/configuration, 'sport' doesn't *have* to only refer to a sport. It could be a League, Event Series, or
basically anything. It might be helpful to think of it just as a way of associating some set of team logos or images to 
create thumbnails from.

Should be a list of objects configuring different sports, where each entry can contain the following:

### `name` *required*

The name of the sport/league/etc.

if the entry does not have any defined `matches`, this is the string used to check for a match to this sport. 

For example, in the sample config above, the `NFL` entry only has its `name` specified. When trying to determine if an 
event should be treated as being an `NFL` event, only 'NFL' will be searched for and matched.

Matches are done case-insensitive, and any spaces present in the name will also match other common filename 
separators such as `.`, `-`, `_`, along with whitespace. For example, the `Formula 1` entry will also 
match `Formula.1`, `formula_1`, and `FORMULA-1`. The match strings are treated more as searches as opposed to exact 
matches in that they are not expected to be the alone, so 'Formula 1' would match against the longer 
string 'FIA Formula 1 Racing'.

### `matches`

An optional collection of strings or objects that will be used to match for the sport instead of `name`.

For simple string matches, basic regex features are supported, and like `name`, searches are done case-insensitive 
and any spaces in the string will also match the common alternative delimiters.

Using an object allows for more specialized handling by allowing you to override the show name for matched episodes.

A match object expects two fields: `match` and `overrideShow`. The `match` field should be a string just as you 
would use for a plain string `match`. `overrideShow` should be a string, which will be used to *override* the show 
name for any episode that matches the match string. 

This can be useful if a given sport might have EPG airings with inconsistent show names. For example, in my EPG data, 
there were multiple separate 'shows' that I wanted to combine under a single Plex show: 'UEFA Nations League', 
'UEFA Nations League Soccer', 'and UEFA Nations League Fútbol'. By using the `overrideShow` option in the match object, 
each of those shows' episodes will have its show name consistently set to 'UEFA Nations League' (when performing 
a meatadata export or move)

### `dateOverride`

I kept running into a problem where EPG data had the wrong air date for a show, and at least for me when this 
happened the wrong date was almost always set to December 31. Setting `dateOverride` lets you control the circumstances where an
episode's EPG metadata 'original' date will be ignored/overridden with the recording date.

There are 3 options: `ALWAYS`, `NEVER`, and `EOY` (End of Year). The default is `EOY`.

If set to `ALWAYS`, any episode that matches the sport will *always* have its date set to the recording date 
(if it can be determined from metadata).

If set to `NEVER`, there will never be any change to whatever EPG/metadata there is for an episode.

If set to `EOY`, if the EPG/metadata air date for an episode is December 31, it will be ignored and the recorded 
date will be used instead.

### `imageRoot`

The root directory to use when searching for team logos. Any subdirectories will also be searched when looking 
for logo images.

### `image`

A specific image to use as the 'generated' thumbnail. Usually only one of `image` or `imageRoot` will be used 
for a given sport entry. You might use `image` instead of `imageRoot` for a sport such as racing where there aren't 
really 'teams', but you still want to have a thumbnail that isn't a video still.

### `background`

Set a sport-level [background style hint](generate.md#background-filename-hinting). 

### `imageTextRegex`

Optional regex that can be used to extract text from an episode title to use when generating the image.

The matching group (if any) is used in thumbnail generation as if it were passed in with a [`--text` argument](generate.md#--text) 

## How sports are matched

During execution, when `pdst` is trying to determine what sport a given event takes place in, 
it will iterate over the list of `sports` entries, and try to find the best match in the file path for the sport 
`name` or `matches`. If multiple equal quality matches are found, the *first* match will be used. 

For example, in the sample configuration above, there is an entry for 'Premier League' as well as 'Soccer'.
If given a file such as `/video/Premier League Soccer/Team A vs. Team B.mkv` to generate an image for, *both* the 
`Premier League` and `Soccer` sport entries will have matches (since the path includes both 
'Premier League' and 'Soccer' exactly). However, since 'Premier League' entry is listed *before* the 'Soccer' entry, 
that is the config that will be used to search for team logos, etc.

However, by having a 'Soccer' entry with an `imageRoot` that is a level *above* Premier League's 
`imageRoot`, that entry will match e.g. 'UEFA Champions League', and when looking for team logos 
will also search the subdirectories which include the Premier League team logos.

This pattern of specific > fallback configuration can be used to group leagues that may have inter-league matches or 
tournaments where league matches will have better chance of picking the correct team logos (given a 
smaller, more precise logo set), but inter-league matches will also be able to find team logos 
without having to have duplicate files

## Program-level configurations

## `imageRoot`

Set a fallback directory to use for finding images in case a sport match is not found. You probably want to use 
the top-level of your logo/image directory structure. If your `sports` section is setup well and has entries 
for all sports that will be encountered when generating images, this will rarely, if ever, be used.

## `thumbnailSize`

Sets the default image size (width, height) used when generating thumbnail images

## `fallbackColor`

Sets the default color used if no colors (from [filename hints](generate.md#image-generation-filename-hinting) or image analysis) can be identified. 
Will likely rarely be used.

## `videoExtensions`

The list of file extensions used as a basic test to determine if a given filename should be considered a video file

## `imageExtensions`

The list of file extensions used as a basic test to determine if a given filename should be considered an image file

## `createdImageExtension`

The extension to use when saving generated images

## `plexLibrary`

The path to the _root_ of your [Plex library](https://support.plex.tv/articles/202915258-where-is-the-plex-media-server-data-directory-located/) 
(data directory - **not** media library!). This is where your metadata database is found.

## `moveTarget`

The root folder of the destination media library that `move` should use when moving media files

## `umask`

Sets the permissions umask when creating files/directories
