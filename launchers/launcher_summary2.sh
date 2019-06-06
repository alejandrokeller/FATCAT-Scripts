#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
today=`date '+%Y%m%d'`
file2="/home/pi/fatcat-files/data/summaries/$today-120s.dat"
cd /FATCAT-scripts/
python /FATCAT-scripts/integrate_co2.py $(ls -t /home/pi/fatcat-files/data/* | head -1) > $file2
cd /
