#!/usr/bin/env python

import argparse      # for argument parsing
import os, sys
import datetime, time
import configparser

import serial
import serial.tools.list_ports
sys.path.append('../extras/')
from tca import serial_ports
from tca import open_tca_port

def send_command(ser, query):
    # This function sends a query to port 'ser' and returns the instrument response
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    print >>sys.stderr, timestamp + "Sending command '" + q + "'"
    ser.write(query)

if __name__ == "__main__":

    description_text= """Prepares fatcat for analysis/sampling."""

    parser = argparse.ArgumentParser(description=description_text)
    mode_parser = parser.add_mutually_exclusive_group(required=True)
    mode_parser.add_argument('--sample', dest='sample', action='store_true',
                    help='set valves/pumps to sample mode.')
    mode_parser.add_argument('--analysis', dest='sample', action='store_false',
                    help='set valves/pumps to zero air.')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                    help='Path to configuration file (../config.ini if omitted)')
    #parser.set_defaults(sample=True)

    args = parser.parse_args()

    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        port_name = eval(config['SERIAL_SETTINGS']['SERIAL_PORT_DESCRIPTION'])
    else:
        port_name = 'nano-TD'
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)


    if args.sample:
        queries = [
            "U0000", # Switch off internal pump
            "V0000", # Switch off internal valve
            "E1000",  # Switch on  external pump
            "L0000" # Switch off external valve
            ]
    else:
        queries = [
            "L1000", # Switch on  external valve
            "E0000", # Switch off external pump
            "V1000", # Switch on  internal valve
            "U1000"  # Switch on  internal pump
            ]
    
    
    ser = open_tca_port(port_name = port_name)
    for q in queries:
        send_command(ser, q)
    ser.close()

    print >>sys.stderr, "bye..."
