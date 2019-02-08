#!/usr/bin/env python

import argparse      # for argument parsing
import configparser
import time
import os,sys

import serial
import serial.tools.list_ports
sys.path.append('../extras/')
from tca import serial_ports
from tca import open_tca_port

if __name__ == "__main__":

    description_text = """Send the list of serial commands to FATCAT. e.g.:
         S1xxx -> 000...999 -> Set target temperature of OVEN;
         S2xxx -> 000...999 -> Set target temperature of BANDheater;
         P1xxx -> 000...100 P-ControlParameter of OVEN;
         P2xxx -> 000...100 P-ControlParameter of BANDHeater;
         Nxxxx -> set the serial number from unit to SN xxxx"""

    parser = argparse.ArgumentParser(description=description_text)
    parser.add_argument('commands', metavar='list',
                    nargs='+',
                    help='<Requiered> List of one or more commands to be transmitted')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                    help='Path to configuration file (../config.ini if omitted)')

    args = parser.parse_args()

    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        port_name = eval(config['SERIAL_SETTINGS']['SERIAL_PORT_DESCRIPTION'])
    else:
        port_name = 'nano-TD'
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    ser = open_tca_port(port_name=port_name)

    for s in args.commands:
        timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
        print timestamp + "Sending command '" + s + "'" 
        ser.write(s)
