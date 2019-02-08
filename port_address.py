#!/usr/bin/env python
# if the adress of the first serial port related to FATCAT (or other 'nano-TD') application
# outputs 'n/a' if no port is found

import serial.tools.list_ports
import sys, os, configparser

sys.path.append('./extras/')
from tca import serial_ports

# READ ini file
config_file = 'config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    port_name = eval(config['SERIAL_SETTINGS']['SERIAL_PORT_DESCRIPTION'])
else:
    port_name = 'nano-TD'  # if ini file cannot be found
    print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

print serial_ports(port_name)
