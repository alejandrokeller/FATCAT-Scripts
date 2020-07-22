#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
cd /FATCAT-scripts/launchers
. ./config
cd ../extras
./day_summary.py --skip-simple --plot-concentration -l $last
./ftp_uploader.py -l
cd /
