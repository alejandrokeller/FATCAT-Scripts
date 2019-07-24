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
            self.serial_baudrate         = eval(config['SERIAL_SETTINGS']['SERIAL_BAUDRATE'])
            self.serial_parity           = eval(config['SERIAL_SETTINGS']['SERIAL_PARITY'])
            self.serial_stopbits         = eval(config['SERIAL_SETTINGS']['SERIAL_STOPBITS'])
            self.serial_bytesize         = eval(config['SERIAL_SETTINGS']['SERIAL_BYTESIZE'])
            self.serial_timeout          = eval(config['SERIAL_SETTINGS']['SERIAL_TIMEOUT'])
            self.uv_constant             = eval(config['CALIBRATION']['UV_CONSTANT'])
        else:
            self.log_message("INSTRUMENT", "Could not find the configuration file: " + config_file)
            exit()

        self.stop_str  = 'X0000'
        self.start_str = 'X1000'
        self.queries = [
            "C?", # Response: "PID1=[value in mv], PID2=[value in mv], to Control PIDx: <ON> = Cx100 or <OFF> = Cx000"
            "E?", # Response: "Status PUMP1=__, PUMP2=__, to Control PUMPx: <ON> = Ex100 or <OFF> = Ex000"
            "F?", # Response: "SetPoint PUMP1=__ PUMP2=__ [%]"
            "L?", # Response: "Control LAMPS 1 to 5: Lx000 (x= uint8 bitwise 0x00054321)"
#            "M?", # Response: "SET MassFlowController 2 = __ [ml]"
            "N?", # Response: "Serial Number=____"
#            "p?", # Response: "Current p Value of control loop = __ ; Set with: p0001 to p0050"
#            "i?", # Response: "Current i Value of control loop = __ ; Set with: i0001 to i0050"
            "P?", # Response: "VOC1 SETPOINT=____ [mV]; Set with: P0000 to P2500"
#            "Q?", # Response: "Tubeheater SETPOINT=__[C]; Set temp with: Q0001 to Q080"
#            "R?", # Response: "RH SETPOINT=___%; Set percentage with: R0000 to R0100"
#            "T?", # Response: "time and date"; // TODO! Not ready yet because of missing battery;
#            "X?", # Response:"Control DATASTREAM: <ON> = X1000 or <OFF> = X0000 \r\n"
            "Z?"  # Response: "LAMP_STATUS_BYTE hexadecimal = 0x00"
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

    def set_pump(self, pump, flow, open_port = False):
        c = 'L'+str(pump)+'{0:03d}'.format(flow)
        if flow >= 0 and flow <= 100 and ( pump == 1 or pump == 2):
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "Pump setting invalid: '" + c + "'")

    def set_mfc2(self, flow, open_port = False): # flow must be in ml
        c = 'M0'+'{0:03d}'.format(flow)
        if flow >= 0 and flow <= 100:
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "MFC setting invalid: '" + c + "'")

    def set_lamps(self, binary_pattern, open_port = False): # i.e. '11111' for all lamps on
        lamps = int(binary_pattern, 2)
        offset = int('01000000',2)
        chr_nr = (lamps ^ offset)
        c = 'L'+ chr(chr_nr) + '000'
        print "sending command: " + c + " chr_nr: " + str(chr_nr)
        if len(c) == 5:
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "Lamp pattern invalid: '" + c + "'")

    def set_voc1(self, mv, open_port = False): # set point in milivolts
        c = 'P'+'{0:04d}'.format(mv)
        if mv > 0 and mv <= 2500:
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "VOC1 setting invalid: '" + c + "'")

    def set_tubeT(self, temperature, open_port = False): # in degC
        c = 'Q'+'{0:04d}'.format(temperature)
        if temperature > 0 and temperature <= 80:
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "Tube temperature setting invalid: '" + c + "'")

    def set_rH(self, rH, open_port = False): # in %rH
        c = 'R'+'{0:04d}'.format(rH)
        if rH > 0 and rH <= 100:
            self.send_commands([c], open_port = open_port)
        else:
            self.log_message("SERIAL", "Relative humidity setting invalid: '" + c + "'")    

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
