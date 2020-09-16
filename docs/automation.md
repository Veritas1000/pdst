# Automation

My automation scripts for reference, these almost certainly won't work for everyone without modification.

## Watch Dir and process

Save as e.g. `/usr/local/sbin/plex_watch`

```bash
#!/usr/bin/env bash

# necessary for CLI
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

export PDST_CFG=/data/media/sports.json
WATCHDIR="/data/media/video/dvr"

echo "Checking for python and pdst..."
python3 --version
pdst --version

inotifywait -m -q -r -e create -e move --format %w%f "${WATCHDIR}" | while IFS= read -r file; do
    dateVal=$(date)
    echo "${dateVal}: ${file}"
    if ffmpeg -hide_banner -i "$file" 2>&1 >/dev/null | grep -q 'Metadata'; then
        if [[ ( $file != *".grab"* ) && ( $file != *"Plex Versions"* ) && ( $file == *".ts" ) ]]; then
            echo "${file} is a .ts video file!"
            outfile="${file/%.ts/.mkv}"
            echo "Converting to ${outfile}"
            ffmpeg -hide_banner -loglevel panic -i "$file" -map 0 -c copy -y "$outfile" &>/dev/null
            
            pdst meta-export -v "$file" && \
            pdst generate -v "$file" && \
            pdst move -v --skip-ext ts "$file"

        fi
    fi
done
```

## Service to run above script

In my server, `data-config.mount` and `data-media.mount` are the drive mounts that are needed for 
plex config and media, respectively, so they need to be available for the service.

Also note that this runs as the same User/Group as plex itself (`media`/`media` for me), so that file permissions 
are not an issue. 

Save as e.g. `/etc/systemd/system/plex_watch.service`

```
[Unit]
Description=Plex library watcher service
After=network.target data-config.mount data-media.mount

[Service]
User=media
Group=media

# WIP
#StandardOutput=append:/var/log/plex_watch.log
#StandardError=append:/var/log/plex_watch.log

ExecStart=/usr/local/sbin/plex_watch
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

## Cleanup libraries

Part of a daily cron job

```bash
echo "Cleaning orphaned metadata files in the sports library"
pdst clean -v -R /data/media/video/sports/

echo "Cleaning old files from DVR Library"
pdst clean -v --older 1w -R /data/media/video/dvr/
```

## FUTURE? Improving Commercial detection / cutting

Externalize the commercial detection so the raw recordings are available in Plex faster, and make 
it non-destructive (in that the original recording is kept available)

1. Run comskip manually?
    - generates .edl and other files
    
2a. If Marking commercials:
    - generate `ffmpeg` or `mkvmerge` chapter file
    - process video to insert chapter markers
2b. If deleting commercials:
    - slice video
    
3. Transcode video with handbrake?
