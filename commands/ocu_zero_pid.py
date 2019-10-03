#!/usr/bin/env python
import sys, os

base_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
sys.path.append(base_path + '/extras/')
from instrument import instrument

config_file = os.path.abspath(base_path + '/config.ini')
device = instrument(config_file = config_file)

device.log_message("COMMANDS", "Setting PID baseline (at current value)...")
device.send_commands(['Z1100'], open_port = True)
