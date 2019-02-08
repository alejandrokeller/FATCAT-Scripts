import time
import serial
import serial.tools.list_ports
import os, configparser

def serial_ports(port_name='nano-TD'):
    # produce a list of all serial ports. The list contains a tuple with the port number,
    # description and hardware address
    #
    ports = list(serial.tools.list_ports.comports())

    # return the port if 'nano-TD' is in the description
    for port in ports:
        if port_name in port[2]:
            return port[0]
    return "n/a"

def open_tca_port(use_sense = 0, port_name='nano-TD'):
    # searches for an available TCA port and opens the serial connection
    # waits 30 seconds before trying again if no port found
    # returns the port object
    tcaport=serial_ports(port_name)

    try:
       while tcaport == "n/a":
          timestamp = time.strftime("%y.%m.%d-%H:%M:%S ")
          print timestamp + "no TCA found, waiting 30 seconds..."
          time.sleep(30)
          tcaport=serial_ports(port_name)
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

def read_serial_port_name(config_file = 'config.ini'):
    # Reads config.ini to determine the serial port name description

    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        port_name = eval(config['SERIAL_SETTINGS']['SERIAL_PORT_DESCRIPTION'])
    else:
        port_name = 'nano-TD'
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    return port_name
