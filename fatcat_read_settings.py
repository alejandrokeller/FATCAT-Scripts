#!/usr/bin/env python

import argparse      # for argument parsing
import os, sys
import datetime
          
execfile("tca.py")

def create_status_file( path = "/home/pi/data/syncaod/fatcat/logs/status/", name = "fatcat_status.txt" ): 
    #This function creates a new datafile name
    prefix = time.strftime("%Y%m%d-%H%M%S-")
    newname = path + prefix + name
    return newname

def query_status(ser, query):
    # This function sends a query to port 'ser' and returns the instrument response
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    print >>sys.stderr, timestamp + "Sending command '" + q + "'"
    ser.write(query)
    answer = ""
    while not answer.endswith("\n"):
        answer=ser.readline()
    return answer

def stop_datastream(ser):
    # This function sends the stop datastream command (X0000) and
    # waits until there is no furter answer
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    print >>sys.stderr, timestamp + "Stopping datastream."
    ser.write('X0000')
    while len(ser.readline()):
        pass

def start_datastream(ser):
    # This function sends the start datastream command (X1000)
    timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
    print >>sys.stderr, timestamp + "Starting datastream."
    ser.write('X1000')

if __name__ == "__main__":

    description_text = """Reads settings of fatcat device.
        Datastreaming is stopped temporary."""

    parser = argparse.ArgumentParser(description=description_text)

    # args = parser.parse_args()

    queries = [
            "A?", # Response:"Duration of next burn cycle in seconds =%i\r\n"
            "B?", # Response:"Status OVEN=%i BAND=%i\r\n"
            "C?", # Response:"Status PUMP=%i SET_FLOW=%i [dl]\r\n"
            "F?", # Response:"FLOW Controller Setpoint is %.1f SLPM\r\n"
#            "L?", # Response:"Control LICOR: <ON> = L1000 or <OFF> = L0000 \r\n"
            "N?", # Response:"Serial Number=%i\r\n"
            "O?", # Response:"Status LICOR=%i VALVE=%i PUMP=%i\r\n"
            "P?", # Response:"P1=%i P2=%i P3=%i\r\n"
            "S?", # Response:"S1=%i S2=%i S3=%i\r\n"
#            "T?", # getDateTimeString(str); RealtimeClock is not implemented yet
                  # Response:(string,"\r\n");
#            "U?", # Response:"Control PUMP: <ON> = U1000 or <OFF>= U0000 \r\n"
#            "V?", # Response:"Control VALVE: <ON> = V1000 or <OFF> = V0000 \r\n"
#            "X?", # Response:"Control DATASTREAM: <ON> = X1000 or <OFF> = X0000 \r\n"
            "Z?"  # Response:"STATUSBYTE HEX = %X \r\n"
            ]
    
    
    ser = open_tca_port()
    stop_datastream(ser)
    fatcat_status = ""
    
    for q in queries:
        fatcat_status += query_status(ser, q)

    print fatcat_status

    newname = create_status_file()
    print >>sys.stderr, "Writing to Datafile: " + newname
    fo = open(newname, "a")
    fo.write(fatcat_status)
    fo.close()

    start_datastream(ser)
    ser.close()

    print >>sys.stderr, "bye..."
