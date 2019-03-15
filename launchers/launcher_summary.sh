#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
today=`date '+%Y%m%d'`
file1="/home/pi/fatcat-files/data/$today-Ambient-Denuder.dat"
file2="/home/pi/fatcat-files/data/summaries/$today-120s.dat"
cd /FATCAT-scripts/
python /FATCAT-scripts/fatcat_integrate_co2.10min.py --intlength 120 $file1 > $file2
cd /
