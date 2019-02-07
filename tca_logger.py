#!/usr/bin/env python

import os, sys
import datetime
from sense_hat import SenseHat

from tcp_interface_class import send_string

execfile("extras/tca.py")
execfile("extras/tca_sense_variables.py")

def create_data_file( path, header = "extras/TCA_Columns.txt", name = "zero-air-licor_before_pump.txt" ): 
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

def sense_sensor_string():
    #this function reads the sense data and prepares a string
    temp     = sense.get_temperature()
    humidity = sense.get_humidity()
    pressure = sense.get_pressure()

    sensor_data = '{:.1f}'.format(humidity) + '\t' + '{:.1f}'.format(temp) + '\t' + '{:.1f}'.format(pressure)
    return sensor_data

# Connect the socket to the port where the server is listening
server_address = ('localhost', 10000)
sock = 0

# Variables
dirname = "data/"
pathname = os.path.dirname(sys.argv[0])
headerpath = os.path.abspath(pathname)
headerfile=headerpath + "/extras/TCA_Columns.txt"
newname=""
buffersize=60

use_sense = 0
sense_count = 3

if use_sense:
	sense = SenseHat()
	sense.show_letter(error_letter)
ser = open_tca_port(use_sense)

counter=0
filedate = datetime.datetime.now()
newname = create_data_file(dirname, header=headerfile)
print "Writing to Datafile: " + newname
print "Using header file: " + headerfile
x=''

print 'starting up on %s port %s' %server_address

while 1:
    try:
       tca_string=ser.readline()
       daytime = time.strftime("%H:%M:%S")
    except serial.serialutil.SerialException:
       ser.close()
       timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
       print timestamp + "cannot read data-line. Restarting port and waiting 5 seconds..."
       if use_sense:
           sense.show_letter(error_letter)
       time.sleep(5)
       ser = open_tca_port(use_sense)
    except KeyboardInterrupt:
       timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
       print timestamp + "aborted by user!"
       ser.close()
       print "Writing data..."
       fo = open(newname, "a")
       fo.write(x)
       fo.close()
       print "bye..."
       if use_sense:
          sense.clear()
       break
    except:
       ser.close()
       timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
       print timestamp + "something went wrong... Restarting port and waiting 5 seconds..."
       print "    --- error type:", sys.exc_info()[0]
       print "    --- error value:", sys.exc_info()[1]
       print "    --- error traceback:", sys.exc_info()[2]
       if use_sense:
           sense.show_letter(error_letter)
       time.sleep(5)
       ser = open_tca_port()       

    if tca_string <> "":
       if use_sense:
          ambient_data = sense_sensor_string()
#          print ambient_data
#          sense.set_pixels(tc_symbol)
#          sense_light = not sense_light
#          sense.low_light = sense_light
          sense.set_pixels(sense_vector[sense_count])
          if sense_count > 0:
             sense_count -= 1
          else:
             sense_count = 3
       x+=daytime + '\t' + tca_string
       # transmit TCP data
       sock = send_string(tca_string, server_address, sock)
#       line = daytime + '\t' + tca_string
#       sock = send_string(line, server_address, sock)
    counter+=1;
    newdate = datetime.datetime.now()

    if newdate.day <> filedate.day:
       if use_sense:
           sense.clear(blue)
       fo = open(newname, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
       filedate = newdate
       newname = create_data_file(dirname, header=headerfile)
       print "Writing to Datafile: " + newname
    elif counter >= buffersize:
       if use_sense:
           sense.clear(green)
       fo = open(newname, "a")
       fo.write(x)
       fo.close()
       x=''
       counter=0
