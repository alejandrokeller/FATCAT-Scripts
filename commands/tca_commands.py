#!/usr/bin/env python

import argparse      # for argument parsing
import configparser
import time
import os, sys

import serial
import serial.tools.list_ports
sys.path.append('../extras/')
from instrument import instrument

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Send serial commands to FATCAT.')
    parser.add_argument('--set-flow', required=False, dest='flowrate', type=int,
                    help='Set the instrument flow in deciliter per minute (0 to 20)')
    parser.add_argument('--set-eflow', required=False, dest='eflowrate', type=int,
                    help='Set the external flow in deciliter per minute (0 to 170)')
    parser.add_argument('--countdown', required=False, dest='seconds', type=int,
                    help='Set burn cycle time in seconds (0-80)')
    parser.add_argument('--band', required=False, dest='band_status',
                    help='Set the status of the band heater (on or off)')
    parser.add_argument('--licor', required=False, dest='licor_status',
                    help='Set the status of the licor (on or off)')
    parser.add_argument('--pump', required=False, dest='pump_status',
                    help='Set the status of the pump (on or off)')
    parser.add_argument('--extpump', required=False, dest='ext_pump_status',
                    help='Set the status of the pump (on or off)')
    parser.add_argument('--data', required=False, dest='datastream_status',
                    help='Stop or restarts datastream (off or on); response to commands are still transmitted.')
    parser.add_argument('--valve', required=False, dest='valve_status',
                    help='Set the status of the valve (on or off)')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                    help='Path to configuration file (../config.ini if omitted)')

    args = parser.parse_args()

    config_file = args.INI
    device = instrument(config_file)
    device.open_port()
    
    queries = []

    timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")

    if args.flowrate > 20:
        print "ERROR: valid flow range is 0 to 20 dl per minute." 
    elif args.flowrate >= 0:
        flow = 'F{:04d}'.format(args.flowrate)
        print timestamp + "Setting pump flow rate to " + flow 
        queries.append(flow)
#    elif args.flowrate < 0:
#        print "ERROR: flow must be larger than 0."

    if args.eflowrate > 170:
        print "ERROR: valid flow range is 0 to 170 dl per minute." 
    elif args.eflowrate >= 0:
        flow = 'C{:04d}'.format(args.eflowrate)
        print timestamp + "Setting external pump flow rate to " + flow 
        queries.append(flow)
#    elif args.eflowrate < 0:
#        print "ERROR: flow must be larger than 0."

    if args.seconds > 80:
        print "ERROR: valid countdown range is 0 to 80 seconds."
    elif args.seconds:
        if args.seconds > 0:
            seconds = 'A{:04d}'.format(args.seconds)
            print timestamp + "Setting countdown to " + seconds + "seconds"
            queries.append(seconds)
        else:
            print "ERROR: countdown must be larger than 0."


    if args.pump_status == 'on':
        print timestamp + "Switching pump ON."
        queries.append('U1000')
    elif args.pump_status == 'off':
        print timestamp + "Switching pump OFF."
        queries.append('U0000')
    elif args.pump_status:
        print "ERROR: Valid pump-status: on and off."
        
    if args.ext_pump_status == 'on':
        print timestamp + "Switching external pump ON."
        queries.append('E1000')
    elif args.ext_pump_status == 'off':
        print timestamp + "Switching external pump OFF."
        queries.append('E0000')
    elif args.ext_pump_status:
        print "ERROR: Valid ext_pump-status: on and off."

    if args.datastream_status == 'on':
        print timestamp + "Restarting datastream."
        queries.append('X1000')
    elif args.datastream_status == 'off':
        print timestamp + "Stopping datastream."
        queries.append('X0000')
    elif args.datastream_status:
        print "ERROR: Valid datastream-status: on and off."

    if args.valve_status == 'on':
        print timestamp + "Switching valve ON."
        queries.append('V1000')
    elif args.valve_status == 'off':
        print timestamp + "Switching valve OFF."
        queries.append('V0000')
    elif args.valve_status:
        print "ERROR: Valid valve-status: on and off."

    if args.band_status == 'on':
        print timestamp + "Switching band heater ON."
        queries.append('B1000')
    elif args.band_status == 'off':
        print timestamp + "Switching band heater OFF."
        queries.append('B0000')
    elif args.band_status:
        print "ERROR: Valid band-status: on and off."

    if args.licor_status == 'on':
        print timestamp + "Switching LICOR ON."
        queries.append('L1000')
    elif args.licor_status == 'off':
        print timestamp + "Switching LICOR OFF."
        queries.append('L0000')
    elif args.licor_status:
        print "ERROR: Valid licor-status: on and off."

    device.send_commands(queries)
    device.close_port()
