#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home
cd /FATCAT-scripts/
python /FATCAT-scripts/fatcat_integrate_co2.10min.py --intlength 120 --last $(ls -t /home/pi/fatcat-files/data/* | head -1)
cd /
