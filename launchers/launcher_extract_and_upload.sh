#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
cd /GAW-Instrument
today=`date '+%Y%m%d'`
filename="/home/pi/fatcat-files/data/$today.dat"
python export-day.py > $filename
cd /FATCAT-scripts/
python /FATCAT-scripts/fatcat_integrate_co2.10min.py --intlength 120 --upload --last $filename
cd /
