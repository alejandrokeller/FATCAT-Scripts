#!/usr/bin/env python
import time, sys

sys.path.append('../extras/')
from instrument import instrument

config_file = '../config.ini'
device = instrument(config_file)

device.log_message("COMMANDS", "Turning induction oven on...")
device.send_commands(['O1000'], open_port = True)


