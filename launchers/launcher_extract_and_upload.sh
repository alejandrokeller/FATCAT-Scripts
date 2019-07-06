#!/bin/sh
# launcher_extract_and_upload.sh
# This launcher is used in case the data is located in the local backup of the cloud application
# navigate to home directory, then to this directory, then execute python script, then back home
cd /FATCAT-scripts/launchers
. ./config
cd /GAW-Instrument
python export-day.py > $newfile
cd /FATCAT-scripts/
python /FATCAT-scripts/extract.py --no-header --upload --last $newfile >> $file2
cd /
