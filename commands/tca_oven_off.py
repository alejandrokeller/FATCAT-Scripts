#!/usr/bin/env python

execfile("../extras/tca.py")

ser = open_tca_port(read_serial_port_name(config_file = '../config.ini'))

timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
print timestamp + "Turning induction oven off..."

ser.write('O0000')
