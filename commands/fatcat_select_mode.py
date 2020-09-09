#!/usr/bin/env python

import argparse, sys, os      # for argument parsing

base_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
sys.path.append(base_path + '/extras/')
from instrument import instrument

if __name__ == "__main__":

    description_text= """Prepares fatcat for analysis/sampling."""

    config_file = os.path.abspath(base_path + '/config.ini')

    parser = argparse.ArgumentParser(description=description_text)
    mode_parser = parser.add_mutually_exclusive_group(required=True)
    mode_parser.add_argument('--sample', dest='sample', action='store_true',
                    help='set valves/pumps to sample mode.')
    mode_parser.add_argument('--analysis', dest='sample', action='store_false',
                    help='set valves/pumps to zero air.')
    parser.add_argument('--standby', required=False, dest='standby', action='store_true',
                    help='Switch off pumps and close sample and external valves. Has priority over other arguments.')
    bypass_parser = parser.add_mutually_exclusive_group(required=False)
    bypass_parser.add_argument('--bypass', dest='bypass', action='store_true',
                    help='do not switch off external pump during analysis.')
    bypass_parser.add_argument('--normal', dest='bypass', action='store_false',
                    help='switch off external pump during analysis (default).')
    parser.add_argument('--inifile', required=False, dest='INI', default=config_file,
                    help='Path to configuration file ({} if omitted)'.format(config_file) )
    parser.set_defaults(bypass=False)
    zero_parser = parser.add_mutually_exclusive_group(required=False)
    zero_parser.add_argument('--analysis_inlet', dest='zero', action='store_true',
                    help='use analysis air inlet for sample collection.')
    zero_parser.add_argument('--sample_inlet', dest='zero', action='store_false',
                    help='use sample inlet  for sample collection (default).')
    parser.set_defaults(zero=False)

    args = parser.parse_args()

    config_file = args.INI
    device = instrument(config_file = config_file)

    if args.standby:
        queries = [
            "U0000", # Switch off internal pump
            "V1000", # Switch on internal valve
            "E0000",  # Switch off external pump
            "L0000" # Switch off external valve
            ]
    else:
        if args.sample:
            if args.zero:
                if args.bypass:
                    queries = [
                        "U0000", # Switch off internal pump
                        "V1000", # Switch on internal valve
                        "E1000",  # Switch on  external pump
                        "L0000" # Switch off external valve
                        ]
                else:
                    queries = [
                        "U1000", # Switch on internal pump
                        "V1000", # Switch on internal valve
                        "E0000",  # Switch off external pump
                        "L0000" # Switch off external valve
                        ]
            else:
                queries = [
                    "U0000", # Switch off internal pump
                    "V0000", # Switch off internal valve
                    "E1000",  # Switch on  external pump
                    "L0000" # Switch off external valve
                    ]
        else:
            if args.bypass:
                queries = [
                    "L1000", # Switch on  external valve
                    "E1000", # Switch on external pump
                    "V1000", # Switch on  internal valve
                    "U1000"  # Switch on  internal pump
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
