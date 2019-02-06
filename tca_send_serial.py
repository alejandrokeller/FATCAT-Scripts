#!/usr/bin/env python

import argparse      # for argument parsing
          
execfile("tca.py")

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

    args = parser.parse_args()

    ser = open_tca_port()

    for s in args.commands:
        timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
        print timestamp + "Sending command '" + s + "'" 
        ser.write(s)
