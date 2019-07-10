#!/bin/sh
# launcher_sample_mode.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts/commands
./serial_commands.py --pump off
./serial_commands.py --extpump on
cd /
