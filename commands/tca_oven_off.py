#!/usr/bin/env python
import sys

sys.path.append('../extras/')
from instrument import instrument

config_file = '../config.ini'
device = instrument(config_file)
device.log_message("COMMANDS", "Turning induction oven off...")
device.send_commands(['O0000'], open_port = True)
