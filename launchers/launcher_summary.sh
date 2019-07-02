#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
today=`date '+%Y%m%d'`
file1="/home/alejandro/fatcat-files/data/$today-Ambient-Denuder.dat"
file2="/home/alejandro/fatcat-files/data/summaries/$today-120s.dat"
cd /FATCAT-scripts/
python /FATCAT-scripts/integrate_co2.py $file1 > $file2
cd /
