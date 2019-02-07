#!/usr/bin/env python
# python script for testing the transmission of data over TCP
# The script uses aa sample datafile instead of using the intrument's data

import time
import os, sys

from ../tcp_class_widgets import send_string

# Connect the socket to the port where the server is listening
server_address = ('localhost', 10000)
sock = 0

datafile = "SampleData.txt"
fi = open(datafile, "r")

i = 0

for line in fi:
   if (i > 2):
       datastring = line.rstrip('\n')
       daytime, datastring = datastring.split('\t', 1)
       #print >>sys.stderr, line.rstrip('\n')
       print >>sys.stderr, datastring
       # Send data
       #sock = send_string(line, server_address, sock)
       sock = send_string(datastring, server_address, sock)
       time.sleep(0.25)
   else:
       i += 1
fi.close()
