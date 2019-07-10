#!/usr/bin/env python

import argparse      # for argument parsing
import sys, os

base_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
sys.path.append(base_path + '/extras/')
from instrument import instrument

if __name__ == "__main__":

    config_file = os.path.abspath(base_path + "/config.ini")
    
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
    parser.add_argument('--inifile', required=False, dest='INI', default=config_file,
                    help="Path to configuration file ({} if omitted)".format(config_file))

    args = parser.parse_args()

    config_file = args.INI
    device = instrument(config_file = config_file)

    device.open_port()

    for s in args.commands:
        device.log_message("COMMANDS", "Sending command '" + s + "'") 
        device.send_commands([s])
