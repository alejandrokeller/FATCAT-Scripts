import time
import serial
import serial.tools.list_ports
import os, sys, configparser

class instrument(object):
    def __init__(self, config_file):

        self.port = "n/a"

        # Read the name of the serial port
        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            self.serial_port_description = eval(config['SERIAL_SETTINGS']['SERIAL_PORT_DESCRIPTION'])
            self.serial_baudrate = eval(config['SERIAL_SETTINGS']['SERIAL_BAUDRATE'])
            self.serial_parity = eval(config['SERIAL_SETTINGS']['SERIAL_PARITY'])
            self.serial_stopbits = eval(config['SERIAL_SETTINGS']['SERIAL_STOPBITS'])
            self.serial_bytesize = eval(config['SERIAL_SETTINGS']['SERIAL_BYTESIZE'])
            self.serial_timeout = eval(config['SERIAL_SETTINGS']['SERIAL_TIMEOUT'])
        else:
            self.log_message("INSTRUMENT", "Could not find the configuration file: " + config_file)
            exit()

        self.stop_str  = 'X0000'
        self.start_str = 'X1000'
        self.queries = [
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

    def serial_ports(self):
        # produce a list of all serial ports. The list contains a tuple with the port number,
        # description and hardware address
        #
        ports = list(serial.tools.list_ports.comports())

        # return the port if self.serial_port_description is in the description
        for port in ports:
            if self.serial_port_description in port[2]:
                return port[0]
        return "n/a"

    def open_port(self):
        # searches for an available port and opens the serial connection
        # Waits 2 seconds before trying again if no port found
        # and doubles time each try with maximum 32 second waiting time
        # until success or KeyboardInterrupt
        wait = 2

        try:
            while self.port == "n/a":
                self.log_message("SERIAL", "no TCA found, waiting " + str(wait) + " seconds to retry...")
                time.sleep(wait)
                if wait < 32:
                    wait = wait*2
                self.port = self.serial_ports()
        except KeyboardInterrupt:
           self.log_message("SERIAL", "aborted by user!... bye...")
           raise

        self.log_message("SERIAL", "Serial port found: " + str(self.port))

        self.ser = serial.Serial(
            port = self.port,
            baudrate = self.serial_baudrate,
            parity = self.serial_parity,
            stopbits = self.serial_stopbits,
            bytesize = self.serial_bytesize,
            timeout = self.serial_timeout
        )

    def close_port(self):
        self.ser.close()

    def send_commands(self, commands, open_port = False):
        if open_port:
            self.open_port()
        for c in commands:
            self.ser.write(c)
        if open_port:
            self.close_port()

    def stop_datastream(self):
        # This function sends the stop datastream command (X0000) and
        # waits until there is no furter answer
        self.log_message("SERIAL", "Stopping datastream.")
        self.ser.write(self.stop_str)
        while len(self.ser.readline()):
            pass

    def start_datastream(self):
        # This function sends the start datastream command (X1000)
        self.log_message("SERIAL", "Starting datastream.")
        self.ser.write(self.start_str)

    def query_status(self, query):
        # This function sends a query to port 'ser' and returns the instrument response
        self.log_message("SERIAL", "Sending command '" + query + "'")
        self.ser.write(query)
        answer = ""
        while not answer.endswith("\n"):
            answer=self.ser.readline()
        return answer

    def readline(self):
        return self.ser.readline()

    def log_message(self, module, msg):
        """
        Logs a message with standard format
        """
        timestamp = time.strftime("%Y.%m.%d-%H:%M:%S ")
        log_message = "- [{0}] :: {1}"
        log_message = timestamp + log_message.format(module,msg)
        print >>sys.stderr,log_message
