#!/usr/bin/env python

import argparse, sys, os      # for argument parsing

script_path = os.path.dirname(sys.argv[0])
sys.path.append(script_path + '/../extras/')
from instrument import instrument

if __name__ == "__main__":

    description_text= """Prepares fatcat for analysis/sampling."""

    config_file = script_path + '/../config.ini'

    parser = argparse.ArgumentParser(description=description_text)
    mode_parser = parser.add_mutually_exclusive_group(required=True)
    mode_parser.add_argument('--sample', dest='sample', action='store_true',
                    help='set valves/pumps to sample mode.')
    mode_parser.add_argument('--analysis', dest='sample', action='store_false',
                    help='set valves/pumps to zero air.')
    parser.add_argument('--inifile', required=False, dest='INI', default=config_file,
                    "Path to configuration file ({} if omitted)".format(config_file))
    #parser.set_defaults(sample=True)

    args = parser.parse_args()

    config_file = args.INI
    device = instrument(config_file = config_file)

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
    device.log_message("COMMANDS", "Sending commands:" + str(queries))
    device.send_commands(queries)
    device.close_port()
