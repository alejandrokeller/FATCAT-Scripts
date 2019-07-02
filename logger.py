#!/usr/bin/env python

import os, sys
import datetime, time
## from sense_hat import SenseHat
import configparser
import serial
import serial.tools.list_ports

from gui import send_string
sys.path.append('./extras/')
from instrument import instrument

## from sense_interface import sense_interface

def create_data_file(path, header = "extras/columns.txt", name = "datafile.txt" ): 
    #This function creates column headers for a new datafile
    fo      = open(header, "r")
    header  = fo.read()
    fo.close()
    prefix  = time.strftime("%Y%m%d-%H%M%S-")
    date    = time.strftime("%Y-%m-%d")
    newname = path + prefix + name
    fo      = open(newname, "w")
    fo.write(date)
    fo.write('\n')
    fo.write(header)
    fo.close()
    return newname

# READ ini file
config_file = 'config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    data_path = eval(config['GENERAL_SETTINGS']['DATA_PATH']) + '/'
    
    server_name = eval(config['TCP_INTERFACE']['HOST_NAME'])
    server_port = eval(config['TCP_INTERFACE']['HOST_PORT'])
    
    header_file_name = eval(config['LOGGER']['HEADER'])
    buffersize = eval(config['LOGGER']['BUFFER'])
    use_sense = eval(config['LOGGER']['SENSE'])
    basefilename = eval(config['LOGGER']['DATAFILE'])
    extension = eval(config['LOGGER']['EXTENSION'])
    use_serial_number = eval(config['LOGGER']['SN'])
else:
    raise FileNotFoundError(
        errno.ENOENT, os.strerror(errno.ENOENT), config_file)

# Connect the socket to the port where the server is listening
server_address = (server_name, server_port)
sock = 0

# Variables
script_path = os.path.abspath(os.path.dirname(sys.argv[0]))
headerfile=script_path + "/" + header_file_name
counter=0

##if use_sense:
##	sense = sense_interface()
device = instrument(config_file = config_file)
device.open_port()

# Fetch the serial number and establish filename
device.stop_datastream()
str = device.query_status(query='N?').strip() # get serial number
print >>sys.stderr, "Answer to serial number query: '" + str + "'"
device.start_datastream()
for s in str.split("="):
    if s.isdigit(): # parse the number
        serial_number = s
if use_serial_number:
    basefilename = basefilename + '-SN' + serial_number 
basefilename = basefilename + extension

filedate = datetime.datetime.now()
file = create_data_file(data_path, header=headerfile, name=basefilename)
print "Writing to Datafile: " + file
print "Using header file: " + headerfile
x=''

print 'starting up on %s port %s' %server_address

while 1:
    try:
       data_string=device.readline()
       daytime = time.strftime("%H:%M:%S")
    except serial.serialutil.SerialException:
       device.close_port()
       device.log_message("LOGGER", "cannot read data-line. Restarting port and waiting 5 seconds...")
##       if use_sense:
##           sense.error()
       time.sleep(5)
       device.open_port()
    except KeyboardInterrupt:
       device.log_message("LOGGER", "aborted by user!")
       ser.close()
       print "Writing data..."
       fo = open(file, "a")
       fo.write(x)
       fo.close()
       print "bye..."
##       if use_sense:
##          sense.sense.clear()
       break
    except:
       device.close_port()
       device.log_message("LOGGER", "something went wrong... Restarting port and waiting 5 seconds...")
       print "    --- error type:", sys.exc_info()[0]
       print "    --- error value:", sys.exc_info()[1]
       print "    --- error traceback:", sys.exc_info()[2]
##       if use_sense:
##           sense.error()
       time.sleep(5)
       device.open_port()

    if data_string <> "":
##       if use_sense:
##          ambient_data = sense.sense_sensor_string()
##          sense.increase()
       x+=daytime + '\t' + data_string
       # transmit TCP data
       sock = send_string(data_string, server_address, sock)
    counter+=1;
    newdate = datetime.datetime.now()

    # Create a new file at midnight
    if newdate.day <> filedate.day:
##       if use_sense:
##           sense.sense.clear(sense.blue)
       fo = open(file, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
       filedate = newdate
       file = create_data_file(data_path, header=headerfile, name=basefilename)
       print "Writing to Datafile: " + file
    elif counter >= buffersize:
##       if use_sense:
##           sense.sense.clear(sense.green)
       fo = open(file, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
