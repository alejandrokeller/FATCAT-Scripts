#!/usr/bin/env python
import sys, os

script_path = os.path.dirname(sys.argv[0])
sys.path.append(script_path + '/../extras/')
from instrument import instrument

config_file = script_path + '/../config.ini'
device = instrument(config_file = config_file)

device.log_message("COMMANDS", "Turning induction oven on...")
device.send_commands(['O1000'], open_port = True)
