#!/usr/bin/env python

import argparse      # for argument parsing
import os, sys
import datetime
          
execfile("tca.py")

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
    #parser.set_defaults(sample=True)

    args = parser.parse_args()

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
    
    
    ser = open_tca_port()
    for q in queries:
        send_command(ser, q)
    ser.close()

    print >>sys.stderr, "bye..."
