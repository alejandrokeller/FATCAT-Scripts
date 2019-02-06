#!/bin/sh
# launcher_sample_mode.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /home/pi/TCA
python fatcat_select_mode.py --sample
cd /
