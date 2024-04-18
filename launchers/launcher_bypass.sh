#!/bin/sh
# launcher_bypass.sh
# navigate to home directory, then to this directory, then execute python script, then back home
# Set these states:
#   Internal pump:  on
#   Internal valve: on
#   External pump:  on
#   External valve: on

cd /FATCAT-scripts/commands
./fatcat_select_mode.py --analysis --bypass
cd /
