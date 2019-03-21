#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
today=`date '+%Y%m%d'`
file2="/home/pi/fatcat-files/data/summaries/$today-120s.dat"
cd /FATCAT-scripts/
python /FATCAT-scripts/fatcat_integrate_co2.10min.py --intlength 120 $(ls -t /home/pi/fatcat-files/data/* | head -1) > $file2
cd /
