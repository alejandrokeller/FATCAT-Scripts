#!/usr/bin/env python

import argparse      # for argument parsing
import os, sys
import datetime, time
import configparser

import serial
import serial.tools.list_ports
sys.path.append('../extras/')
from instrument import instrument

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
    device = instrument(config_file)

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
    
    
    device.open_port()
    for q in queries:
        device.send_command(q)
    ser.close_port()

    print >>sys.stderr, "bye..."
