#!/usr/bin/env python
# if the adress of the first serial port related to FATCAT (or other 'nano-TD') application
# outputs 'n/a' if no port is found

import serial.tools.list_ports
import sys, os, configparser

script_path = os.path.dirname(sys.argv[0])
sys.path.append(script_path + '/extras/')
from instrument import instrument

# READ ini file
config_file = script_path + '/config.ini'
device = instrument(config_file = config_file)

print device.serial_ports()
