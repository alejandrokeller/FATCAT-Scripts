import time
import serial
import serial.tools.list_ports
from sense_hat import SenseHat

def serial_ports():
    # produce a list of all serial ports. The list contains a tuple with the port number,
    # description and hardware address
    #
    ports = list(serial.tools.list_ports.comports())

    # return the port if 'nano-TD' is in the description
    for port in ports:
        if 'nano-TD' in port[2]:
            return port[0]
    return "n/a"

def open_tca_port(use_sense = 0):
    # searches for an available TCA port and opens the serial connection
    # waits 30 seconds before trying again if no port found
    # returns the port object
    tcaport=serial_ports()

    try:
       while tcaport == "n/a":
          timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
          print timestamp + "no TCA found, waiting 30 seconds..."
          time.sleep(30)
          tcaport=serial_ports()
    except KeyboardInterrupt:
       timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
       print timestamp + "aborted by user!"
       print "bye..."
       if use_sense:
          sense.clear()
       raise


    print "Serial port found: " + tcaport

    ser = serial.Serial(

        port=tcaport,
        baudrate = 115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    return ser

