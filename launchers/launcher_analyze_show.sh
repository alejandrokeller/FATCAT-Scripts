#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
cd /FATCAT-scripts/launchers
. ./config
cd ..
echo "extracting the last event from $file1"
./extract.py --last $file1 
cd /
