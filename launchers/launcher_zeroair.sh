#!/bin/sh
# launcher_zeroair.sh
# navigate to home directory, then to this directory, then execute python script, then back home
# Set these states:
#   Internal pump:  on
#   Internal valve: on
#   External pump:  off
#   External valve: on

cd /FATCAT-scripts/commands
./fatcat_select_mode.py --analysis
cd /
