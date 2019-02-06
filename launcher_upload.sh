#!/bin/sh
# launcher_upload.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /home/pi/TCA/data
python /home/pi/TCA/fatcat_integrate_co2.10min.py --upload --last $(ls -t /home/pi/TCA/data/* | head -1)
cd /
