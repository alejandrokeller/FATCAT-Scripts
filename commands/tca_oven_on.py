#!/usr/bin/env python

execfile("../tca.py")

ser = open_tca_port()

timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
print timestamp + "Turning induction oven on..."

ser.write('O1000')

