#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts/data
./extract.py --upload --last $(ls -t /FATCAT-scripts/data/* | head -1)
cd /
