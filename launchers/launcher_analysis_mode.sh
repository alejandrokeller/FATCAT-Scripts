#!/bin/sh
# launcher_analysis_mode.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts/commands
# Set these states:
#   Internal pump:  on
#   Internal valve: on
#   External pump:  off
#   External valve: on
./fatcat_select_mode.py --analysis
cd /
