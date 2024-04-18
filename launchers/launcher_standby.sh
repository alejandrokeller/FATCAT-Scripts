#!/bin/sh
# launcher_standby.sh
# navigate to home directory, then to this directory, then execute python script, then back home
# Starts modified stadby mode: all pumps off, internal (bypass) and external (analysis air) valves off

cd /FATCAT-scripts/commands
# Set these states:
#   Internal pump:  off
#   Internal valve: on
#   External pump:  off
#   External valve: off
# --analysis is ignored due to --standby
./fatcat_select_mode.py --standby --analysis
# Set these states:
#   Internal valve: off
#   External pump:  off
./serial_commands.py --valve off --extpump off
cd /
