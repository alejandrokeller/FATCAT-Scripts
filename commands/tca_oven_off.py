#!/usr/bin/env python
import time, sys

sys.path.append('../extras/')
from instrument import instrument

config_file = '../config.ini'
device = instrument(config_file)

timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
print timestamp + "Turning induction oven off..."

device.send_commands(['O0000'], open_port = True)
