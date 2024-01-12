#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
cd /FATCAT-scripts/launchers
. ./config
cd ../extras
./day_summary.py --skip-simple --plot-concentration --mute-graphs -s $todayformat
./ftp_uploader.py -s $todayformat
cd /