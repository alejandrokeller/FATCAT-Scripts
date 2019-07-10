#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts
python fatcat_read_settings.py
sleep 3
python logger.py &
cd /
