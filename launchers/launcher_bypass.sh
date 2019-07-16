#!/bin/sh
# launcher_analysis_mode.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts/commands
./fatcat_select_mode.py --analysis --bypass
cd /
