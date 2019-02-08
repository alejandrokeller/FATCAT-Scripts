#!/usr/bin/env python

import argparse      # for argument parsing
import configparser
import time
import os, sys

import serial
import serial.tools.list_ports
sys.path.append('../extras/')
from tca import serial_ports
from tca import open_tca_port

execfile("../extras/tca.py")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Send serial commands to FATCAT.')
    parser.add_argument('--set-flow', required=False, dest='flowrate', type=int,
                    help='Set the instrument flow in deciliter per minute (0 to 20)')
    parser.add_argument('--countdown', required=False, dest='seconds', type=int,
                    help='Set burn cycle time in seconds (0-80)')
    parser.add_argument('--band', required=False, dest='band_status',
                    help='Set the status of the band heater (on or off)')
    parser.add_argument('--licor', required=False, dest='licor_status',
                    help='Set the status of the licor (on or off)')
    parser.add_argument('--pump', required=False, dest='pump_status',
                    help='Set the status of the pump (on or off)')
    parser.add_argument('--data', required=False, dest='datastream_status',
                    help='Stop or restarts datastream (off or on); response to commands are still transmitted.')
    parser.add_argument('--valve', required=False, dest='valve_status',
                    help='Set the status of the valve (on or off)')
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

    timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")

    if args.flowrate > 20:
        print "ERROR: valid flow range is 0 to 20 dl per minute." 
    elif args.flowrate:
        if args.flowrate > 0:
            flow = 'F{:04d}'.format(args.flowrate)
            print timestamp + "Setting pump flow rate to " + flow 
            ser.write(flow)
        else:
            print "ERROR: flow must be larger than 0."

    if args.seconds > 80:
        print "ERROR: valid countdown range is 0 to 80 seconds."
    elif args.seconds:
        if args.seconds > 0:
            seconds = 'A{:04d}'.format(args.seconds)
            print timestamp + "Setting countdown to " + seconds + "seconds"
            ser.write(seconds)
        else:
            print "ERROR: countdown must be larger than 0."


    if args.pump_status == 'on':
        print timestamp + "Switching pump ON."
        ser.write('U1000')
    elif args.pump_status == 'off':
        print timestamp + "Switching pump OFF."
        ser.write('U0000')
    elif args.pump_status:
        print "ERROR: Valid pump-status: on and off."

    if args.datastream_status == 'on':
        print timestamp + "Restarting datastream."
        ser.write('X1000')
    elif args.datastream_status == 'off':
        print timestamp + "Stopping datastream."
        ser.write('X0000')
    elif args.datastream_status:
        print "ERROR: Valid datastream-status: on and off."

    if args.valve_status == 'on':
        print timestamp + "Switching valve ON."
        ser.write('V1000')
    elif args.valve_status == 'off':
        print timestamp + "Switching valve OFF."
        ser.write('V0000')
    elif args.valve_status:
        print "ERROR: Valid valve-status: on and off."

    if args.band_status == 'on':
        print timestamp + "Switching band heater ON."
        ser.write('B1000')
    elif args.band_status == 'off':
        print timestamp + "Switching band heater OFF."
        ser.write('B0000')
    elif args.band_status:
        print "ERROR: Valid band-status: on and off."

    if args.licor_status == 'on':
        print timestamp + "Switching LICOR ON."
        ser.write('L1000')
    elif args.licor_status == 'off':
        print timestamp + "Switching LICOR OFF."
        ser.write('L0000')
    elif args.licor_status:
        print "ERROR: Valid licor-status: on and off."

