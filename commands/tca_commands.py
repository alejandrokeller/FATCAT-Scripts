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

    if args.flowrate > 20:
        print "ERROR: valid flow range is 0 to 20 dl per minute." 
    elif args.flowrate >= 0:
        flow = 'F{:04d}'.format(args.flowrate)
        msg = "Setting pump flow rate to " + flow 
        device.log_message("COMMANDS", msg)
        queries.append(flow)
#    elif args.flowrate < 0:
#        device.log_message("COMMANDS", "ERROR: flow must be larger than 0.")

    if args.eflowrate > 170:
        print "ERROR: valid flow range is 0 to 170 dl per minute." 
    elif args.eflowrate >= 0:
        flow = 'C{:04d}'.format(args.eflowrate)
        msg = "Setting external pump flow rate to " + flow 
        device.log_message("COMMANDS", msg)
        queries.append(flow)
#    elif args.eflowrate < 0:
#        device.log_message("COMMANDS", "ERROR: flow must be larger than 0.")

    if args.seconds > 80:
        device.log_message("COMMANDS", "ERROR: valid countdown range is 0 to 80 seconds.")
    elif args.seconds:
        if args.seconds > 0:
            seconds = 'A{:04d}'.format(args.seconds)
            msg = "Setting countdown to " + seconds + "seconds"
            device.log_message("COMMANDS", msg)
            queries.append(seconds)
        else:
            device.log_message("COMMANDS", "ERROR: countdown must be larger than 0.")


    if args.pump_status == 'on':
        msg = "Switching pump ON."
        device.log_message("COMMANDS", msg)
        queries.append('U1000')
    elif args.pump_status == 'off':
        msg = "Switching pump OFF."
        device.log_message("COMMANDS", msg)
        queries.append('U0000')
    elif args.pump_status:
        device.log_message("COMMANDS", "ERROR: Valid pump-status: on and off.")
        
    if args.ext_pump_status == 'on':
        msg = "Switching external pump ON."
        device.log_message("COMMANDS", msg)
        queries.append('E1000')
    elif args.ext_pump_status == 'off':
        msg = "Switching external pump OFF."
        device.log_message("COMMANDS", msg)
        queries.append('E0000')
    elif args.ext_pump_status:
        device.log_message("COMMANDS", "ERROR: Valid ext_pump-status: on and off.")

    if args.datastream_status == 'on':
        msg = "Restarting datastream."
        device.log_message("COMMANDS", msg)
        queries.append('X1000')
    elif args.datastream_status == 'off':
        msg = "Stopping datastream."
        device.log_message("COMMANDS", msg)
        queries.append('X0000')
    elif args.datastream_status:
        device.log_message("COMMANDS", "ERROR: Valid datastream-status: on and off.")

    if args.valve_status == 'on':
        msg = "Switching valve ON."
        device.log_message("COMMANDS", msg)
        queries.append('V1000')
    elif args.valve_status == 'off':
        msg = "Switching valve OFF."
        device.log_message("COMMANDS", msg)
        queries.append('V0000')
    elif args.valve_status:
        device.log_message("COMMANDS", "ERROR: Valid valve-status: on and off.")

    if args.band_status == 'on':
        msg = "Switching band heater ON."
        device.log_message("COMMANDS", msg)
        queries.append('B1000')
    elif args.band_status == 'off':
        msg = "Switching band heater OFF."
        device.log_message("COMMANDS", msg)
        queries.append('B0000')
    elif args.band_status:
        device.log_message("COMMANDS", "ERROR: Valid band-status: on and off.")

    if args.licor_status == 'on':
        msg = "Switching LICOR ON."
        device.log_message("COMMANDS", msg)
        queries.append('L1000')
    elif args.licor_status == 'off':
        msg = "Switching LICOR OFF."
        device.log_message("COMMANDS", msg)
        queries.append('L0000')
    elif args.licor_status:
        device.log_message("COMMANDS", "ERROR: Valid licor-status: on and off.")

    device.send_commands(queries)
    device.close_port()
