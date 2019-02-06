#!/usr/bin/env python

import serial.tools.list_ports

def serial_ports():

    # produce a list of all serial ports. The list contains a tuple with the port number, 
    # description and hardware address
    #
    ports = list(serial.tools.list_ports.comports())  

    # return the port if 'nano-TD' is in the description 
    for port in ports:
        if 'nano-TD' in port[2]:
            return port[0]

print serial_ports()
