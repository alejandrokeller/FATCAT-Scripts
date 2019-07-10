#!/usr/bin/env python
# python script for testing the transmission of data over TCP
# The script uses a sample datafile instead of using the intrument's data

import time
import os, sys
import configparser

base_path = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
sys.path.append(base_path)

from gui import send_string

# READ ini file
config_file = base_path + '/config.ini'
if os.path.exists(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    host_name = eval(config['TCP_INTERFACE']['HOST_NAME'])
else:
    host_name = 'localhost'
    print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)


# Connect the socket to the port where the server is listening
server_address = (host_name, 10000)
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
       time.sleep(0.5)
   else:
       i += 1
fi.close()
