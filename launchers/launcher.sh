#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts
./fatcat_read_settings.py
sleep 3
./logger.py
cd /
