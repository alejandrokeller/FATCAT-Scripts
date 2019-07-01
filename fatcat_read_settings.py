#!/usr/bin/env python

import argparse      # for argument parsing
import os, sys
import datetime
import configparser

import time
import serial
import serial.tools.list_ports

sys.path.append('./extras/')
from instrument import instrument

def create_status_file( path = "logs/status/", name = "fatcat_status.txt" ): 
    #This function creates a new datafile name
    prefix = time.strftime("%Y%m%d-%H%M%S-")
    newname = path + prefix + name
    return newname

if __name__ == "__main__":

    description_text = """Reads settings of fatcat device.
        Datastreaming is stopped temporary."""

    parser = argparse.ArgumentParser(description=description_text)
    
    # READ ini file
    config_file = 'config.ini'
    device = instrument(config_file)


    device.open_port()
    device.stop_datastream()
    fatcat_status = ""

    for q in device.queries:
        fatcat_status += device.query_status(q)

    device.start_datastream()
    device.close_port()

    print fatcat_status

    newname = create_status_file(path=logs_path)
    print >>sys.stderr, "Writing to Datafile: " + newname
    fo = open(newname, "a")
    fo.write(fatcat_status)
    fo.close()

    print >>sys.stderr, "bye..."
