#!/bin/sh
# launcher_sample_mode.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /FATCAT-scripts/commands
python tca_commands.py --extpump off
python tca_commands.py --pump on
cd /
