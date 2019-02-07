#!/usr/bin/env python
# -*- coding: utf-8 -*-

execfile("extras/tca.py")

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import socket
import sys
import ast # for datastring parsing
import numpy as np

from collections import namedtuple

def hex2bin(s):
    hex_table = ['0000', '0001', '0010', '0011',
                 '0100', '0101', '0110', '0111',
                 '1000', '1001', '1010', '1011',
                 '1100', '1101', '1110', '1111']
    bits = ''
    for i in range(len(s)):
        bits += hex_table[int(s[i], base=16)]
    return bits

def send_string(line, server_address, sock = 0):
    # Sends a string to through a TCP socket

    # Send data
    try:
        if not sock:
            # Create a TCP/IP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

##            print >>sys.stderr, 'Sending data to %s port %s' % server_address
            sock.connect(server_address)
            
        sock.sendall(line)
    except socket.error:
##        print >>sys.stderr, "nobody listening"
        sock.close()
##        print >>sys.stderr, 'closing socket'
        sock = 0

    return sock

class Visualizer(object):
    def __init__(self):

        # init socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
        self.server_address = ('FatCat', 10000)
        print >>sys.stderr, 'starting up on %s port %s' % self.server_address
        self.sock.bind(self.server_address) # Bind the socket to the port
        self.sock.listen(1) # Listen for incoming connections
        print >>sys.stderr, 'waiting for a connection'
        self.connection, self.client_address = self.sock.accept() # Wait for a connection
        print >>sys.stderr, 'connection from', self.client_address

        # init pyqt
        self.app = QtGui.QApplication([])
###        self.win = pg.GraphicsWindow(title="TC Analyzer")
###        self.win.showFullScreen()
###        self.win.setWindowTitle('TC Analyzer')
        pg.setConfigOptions(antialias=False)
        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.numSamples = 2400 
        self.datastring = ""
        
        self.keys = [
            "runtime",
            "spoven",
            "toven",
            "spcoil",
            "tcoil",
            "spband",
            "tband",
            "spcat",
            "tcat",
            "tco2",
            "pco2",
            "co2",
            "flow",
            "curr",
            "countdown"]
        self.tcaData = namedtuple("tcaData", self.keys)
        self.units = self.tcaData(
            "s",    # runtime
            "°C",   # spoven
            "°C",   # toven
            "°C",   # spcoil
            "°C",   # tcoil
            "°C",   # spband
            "°C",   # tband
            "°C",   # spcat
            "°C",   # tcat
            "°C",   # tco2
            "kPa",  # pco2
            "ppm",  # co2
            "lpm",  # flow
            "A",    # current
            "S")    # countdown
            
        self.statusKeys = [
            "valve",
            "pump",
            "fan",
            "oven",
            "band",
            "licor",
            "res2",
            "res"]
        self.statusData = namedtuple("statusData", self.statusKeys)

        self.streamVarsData = self.tcaData._make(np.zeros((np.shape(self.keys)[0],self.numSamples)))
        self.statusVarsData = self.statusData._make(np.zeros((np.shape(self.statusKeys)[0],self.numSamples)))

        # setup plots
        self.deltaT = 0.25 # s, sampling time
        self.pen = pg.mkPen('y', width=1)
        self.t = np.linspace(-self.deltaT*self.numSamples, 0, self.numSamples)

        self.Tcurves = dict()

###        self.Tplot = self.win.addPlot(row=0, col=0, title="")
        self.Tplot = pg.PlotWidget()
        self.Tplot.addLegend()
        self.Tplot.setRange(yRange=[0, 900])
        self.Tplot.setLabel('left', "Temperature", units='°C')
        self.Tplot.setLabel('bottom', "t", units='s')
        self.Tplot.showGrid(False, True)
        self.Tcurves[0] = self.Tplot.plot(self.t, self.streamVarsData.spoven, pen=pg.mkPen('y', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[1] = self.Tplot.plot(self.t, self.streamVarsData.toven, pen=pg.mkPen('y', width=1), name='Oven')
        self.Tcurves[2] = self.Tplot.plot(self.t, self.streamVarsData.spcoil, pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[3] = self.Tplot.plot(self.t, self.streamVarsData.tcoil, pen=pg.mkPen('r', width=1), name='Coil')
        self.Tcurves[4] = self.Tplot.plot(self.t, self.streamVarsData.spband, pen=pg.mkPen('b', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[5] = self.Tplot.plot(self.t, self.streamVarsData.tband, pen=pg.mkPen('b', width=1), name='Band')
        self.Tcurves[6] = self.Tplot.plot(self.t, self.streamVarsData.spcat, pen=pg.mkPen('g', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[7] = self.Tplot.plot(self.t, self.streamVarsData.tcat, pen=pg.mkPen('g', width=1), name='Cat')
#        self.win.nextRow()

        self.Pcurves = dict()

###        self.Pplot = self.win.addPlot(row=3, col=0, title="")
        self.Pplot = pg.PlotWidget()
        self.Pplot.setRange(yRange=[50, 100])
        self.Pplot.setLabel('left', "CO2 Press.", units='kPa')
        self.Pplot.setLabel('bottom', "t", units='s')
        self.Pplot.showGrid(False, True)
        self.Pcurves[0] = self.Pplot.plot(self.t, self.streamVarsData.pco2, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Ccurves = dict()

###        self.Cplot = self.win.addPlot(row=2, col=0, title="")
        self.Cplot = pg.PlotWidget()
#        self.Cplot.setRange(yRange=[0, 100])
        self.Cplot.setLabel('left', "CO2", units='ppm')
        self.Cplot.setLabel('bottom', "t", units='s')
        self.Cplot.showGrid(False, True)
        self.Ccurves[0] = self.Cplot.plot(self.t, self.streamVarsData.co2, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Fcurves = dict()

###        self.Fplot = self.win.addPlot(row=4, col=0, title="")
        self.Fplot = pg.PlotWidget()
        self.Fplot.setRange(yRange=[0, 2])
        self.Fplot.setLabel('left', "Flow", units='lpm')
        self.Fplot.setLabel('bottom', "t", units='s')
        self.Fplot.showGrid(False, True)
        self.Fcurves[0] = self.Fplot.plot(self.t, self.streamVarsData.flow, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

#####################################################################

        ## Define a top level widget to hold the controls
        self.widgets = QtGui.QWidget()
        self.widgets.setWindowTitle("FATCAT: Total Carbon Analizer")
        self.widgets.showFullScreen()

        ## Create infotext widgets to be placed inside
        self.lblLicor     = QtGui.QLabel("Ext. Valve")
        self.lblBand      = QtGui.QLabel("Band Heater")
        self.lblOven      = QtGui.QLabel("Oven")
        self.lblFan       = QtGui.QLabel("Fan")
        self.lblPump      = QtGui.QLabel("Pump")
        self.lblValve     = QtGui.QLabel("Int. Valve")
        self.lblRes2      = QtGui.QLabel("Ext. Pump")
        self.lblRes       = QtGui.QLabel("Res")
        self.lblSample    = QtGui.QLabel("Sample")
        self.lblZeroAir   = QtGui.QLabel("Zero Air")
        
        self.lblCD        = QtGui.QLabel("0")

        ## Create button widgets for actions
        self.button_size = 30
        self.btnPump      = QtGui.QPushButton("")            # Turn internal pump on/off
        self.btnPump.setFixedWidth(self.button_size)
        self.btnBand      = QtGui.QPushButton("")            # Turn Cat. Heating on/off
        self.btnBand.setFixedWidth(self.button_size)
        self.btnValve     = QtGui.QPushButton("")            # Toggle sampling/clean-air valves
        self.btnValve.setFixedWidth(self.button_size)
        self.btnLicor     = QtGui.QPushButton("")            # Toggle external valve
        self.btnLicor.setFixedWidth(self.button_size)
        self.btnOven      = QtGui.QPushButton("!")           # Turn Induction Heating on/off
        self.btnOven.setFixedWidth(self.button_size)
        self.btnRes2      = QtGui.QPushButton("")            # Turn external pump on/off
        self.btnRes2.setFixedWidth(self.button_size)
        self.btnSample    = QtGui.QPushButton("")            # activate sampling mode
        self.btnSample.setFixedWidth(self.button_size)
        self.btnZeroAir   = QtGui.QPushButton("")            # prepare for analisys
        self.btnZeroAir.setFixedWidth(self.button_size)

        self.btnPump.clicked.connect(self.togglePump)
        self.btnBand.clicked.connect(self.toggleBand)
        self.btnValve.clicked.connect(self.toggleValve)
        self.btnLicor.clicked.connect(self.toggleLicor)
        self.btnOven.clicked.connect(self.toggleOven)
        self.btnRes2.clicked.connect(self.toggleRes2)
        self.btnSample.clicked.connect(self.startSample)
        self.btnZeroAir.clicked.connect(self.startZeroAir)

        ## Create a grid layout to manage the controls size and position
        self.controlsLayout = QtGui.QGridLayout()
        self.encloserLayout = QtGui.QVBoxLayout()
        self.encloserLayout.addLayout(self.controlsLayout)
        self.encloserLayout.addStretch(1)

        ## Add widgets to the layout in their proper positions
        self.controlsLayout.addWidget(self.lblPump,    0, 1)
        self.controlsLayout.addWidget(self.lblBand,    1, 1)
        self.controlsLayout.addWidget(self.lblOven,    2, 1)
        self.controlsLayout.addWidget(self.lblValve,   3, 1)
        self.controlsLayout.addWidget(self.lblLicor,   4, 1)
        self.controlsLayout.addWidget(self.lblRes2,    5, 1)
        self.controlsLayout.addWidget(self.lblFan,     7, 0)
        self.controlsLayout.addWidget(self.lblRes,     7, 1)
        self.controlsLayout.addWidget(self.lblSample,  9, 1)
        self.controlsLayout.addWidget(self.lblZeroAir,10, 1)

        self.controlsLayout.addWidget(self.lblCD,    8, 0, 1, 2)

        self.controlsLayout.addWidget(self.btnPump,     0, 0)
        self.controlsLayout.addWidget(self.btnBand,     1, 0)
        self.controlsLayout.addWidget(self.btnOven,     2, 0)
        self.controlsLayout.addWidget(self.btnValve,    3, 0)
        self.controlsLayout.addWidget(self.btnLicor,    4, 0)
        self.controlsLayout.addWidget(self.btnRes2,     5, 0)
        #self.controlsLayout.addWidget(self.btnOven,  7, 0, 1, 2)
        self.controlsLayout.addWidget(self.btnSample,   9, 0)
        self.controlsLayout.addWidget(self.btnZeroAir, 10, 0)

        ## Create a QVBox layout to manage the plots
        self.plotLayout = QtGui.QVBoxLayout()

        self.plotLayout.addWidget(self.Tplot)
        self.plotLayout.addWidget(self.Cplot)
        self.plotLayout.addWidget(self.Pplot)
        self.plotLayout.addWidget(self.Fplot)

        ## Create a QHBox layout to manage the plots
        self.centralLayout = QtGui.QHBoxLayout()

        self.centralLayout.addLayout(self.encloserLayout)
        self.centralLayout.addLayout(self.plotLayout)

        ## Display the widget as a new window
        self.widgets.setLayout(self.centralLayout)
        self.widgets.show()

    def update(self):

        try: 
            self.datastring = self.connection.recv(1024)

            if self.datastring:
##                self.daytime, self.datastring = self.datastring.split('\t', 1)
                ####### syntax changed for the status byte... ignore
                ####### additional variables at the end
                # self.datavector = [ast.literal_eval(s) for s in self.datastring.split( )]
                i = 0
                self.datavector = []
                for s in self.datastring.split( ):
                    if i < len(self.keys):
                         #### use this values als integers
                         self.datavector.append(ast.literal_eval(s))
                    else:
                        try:
                             #### transcode the last value from hex to a binary array
                             self.statusbyte = hex2bin(s)
                             j = 0
                             #### now store it in the status variables
                             for k in self.statusKeys:
                                 self.tempArray = np.roll(self.statusVarsData[j], -1)
                                 self.tempArray[-1] = int(self.statusbyte[j])                             
                                 self.statusVarsData = self.statusVarsData._replace(**{k:self.tempArray})
                                 j += 1
                             break
                        except:
                            pass
                    i += 1
                    
                i = 0
                for k in self.keys:
                    self.tempArray = np.roll(self.streamVarsData[i], -1)
                    self.tempArray[-1] = self.datavector[i]
                    self.streamVarsData = self.streamVarsData._replace(**{k:self.tempArray})
                    i += 1
##                print >>sys.stderr, self.streamVarsData.runtime
                self.Tcurves[0].setData(self.t, self.streamVarsData.spoven)
                self.Tcurves[1].setData(self.t, self.streamVarsData.toven)
                self.Tcurves[2].setData(self.t, self.streamVarsData.spcoil)
                self.Tcurves[3].setData(self.t, self.streamVarsData.tcoil)
                self.Tcurves[4].setData(self.t, self.streamVarsData.spband)
                self.Tcurves[5].setData(self.t, self.streamVarsData.tband)
                self.Tcurves[6].setData(self.t, self.streamVarsData.spcat)
                self.Tcurves[7].setData(self.t, self.streamVarsData.tcat)

                self.Pcurves[0].setData(self.t, self.streamVarsData.pco2)

                self.Ccurves[0].setData(self.t, self.streamVarsData.co2)

                self.Fcurves[0].setData(self.t, self.streamVarsData.flow)
                
####################################################################

                self.lblCD.setText(" ".join(("Countdown:", str(int(self.streamVarsData.countdown[-1])))))
                self.lblOven.setText("".join(("Oven: ", str(int(self.streamVarsData.toven[-1])), "/",
                                              str(int(self.streamVarsData.spoven[-1])), " degC")))
                self.lblBand.setText("".join(("Band: ", str(int(self.streamVarsData.tband[-1])), "/",
                                               str(int(self.streamVarsData.spband[-1])), " degC")))
                self.lblPump.setText("".join(("Pump (", "{:.2f}".format(self.streamVarsData.flow[-1]), " lpm)")))

                if (self.streamVarsData.countdown[-1] % 2 == 0):
                    self.lblCD.setStyleSheet('color: black')
                else:
                    self.lblCD.setStyleSheet('color: red')
                
                if self.statusVarsData.oven[-1]:
                    self.lblOven.setStyleSheet('color: green')
                else:
                    self.lblOven.setStyleSheet('color: red')

                if self.statusVarsData.band[-1]:
                    self.lblBand.setStyleSheet('color: green')
                else:
                    self.lblBand.setStyleSheet('color: red')

                if self.statusVarsData.fan[-1]:
                    self.lblFan.setStyleSheet('color: green')
                else:
                    self.lblFan.setStyleSheet('color: red')

                if self.statusVarsData.pump[-1]:
                    self.lblPump.setStyleSheet('color: green')
                else:
                    self.lblPump.setStyleSheet('color: red')

                if self.statusVarsData.licor[-1]:
                    self.lblLicor.setStyleSheet('color: green')
                else:
                    self.lblLicor.setStyleSheet('color: red')

                if self.statusVarsData.valve[-1]:
                    self.lblValve.setStyleSheet('color: green')
                else:
                    self.lblValve.setStyleSheet('color: red')

                if self.statusVarsData.res[-1]:
                    self.lblRes.setStyleSheet('color: green')
                else:
                    self.lblRes.setStyleSheet('color: red')

                if self.statusVarsData.res2[-1]:
                    self.lblRes2.setStyleSheet('color: green')
                else:
                    self.lblRes2.setStyleSheet('color: red')

                if (not self.statusVarsData.pump[-1] and not self.statusVarsData.valve[-1] and
                        self.statusVarsData.res2[-1]    and not self.statusVarsData.licor[-1]):
                    self.lblSample.setStyleSheet('color: green')
                else:
                    self.lblSample.setStyleSheet('color: red')

                if (self.statusVarsData.pump[-1]     and self.statusVarsData.valve[-1] and
                    not self.statusVarsData.res2[-1] and self.statusVarsData.licor[-1]):
                    self.lblZeroAir.setStyleSheet('color: green')
                else:
                    self.lblZeroAir.setStyleSheet('color: red')
                
        except Exception as e:
            print >>sys.stderr, e
##            raise

    def togglePump(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.pump[-1]:
            ser.write('U0000')
        else:
            ser.write('U1000')
        ser.close()

    def toggleBand(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.band[-1]:
            ser.write('B0000')
        else:
            ser.write('B1000')
        ser.close()

    def toggleValve(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.valve[-1]:
            ser.write('V0000')
        else:
            ser.write('V1000')
        ser.close()

    def toggleLicor(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.licor[-1]:
            ser.write('L0000')
        else:
            ser.write('L1000')
        ser.close()

    def toggleOven(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.oven[-1]:
            ser.write('O0000')
        else:
            ser.write('O1000')
        ser.close()

    def toggleRes2(self):
        # find out which serial port is connected
        ser = open_tca_port()
        if self.statusVarsData.res2[-1]:
            ser.write('E0000')
        else:
            ser.write('E1000')
        ser.close()

    def startSample(self):
        # find out which serial port is connected
        ser = open_tca_port()
        ser.write('U0000')
        ser.write('V0000')
        ser.write('E1000')
        ser.write('L0000')
        ser.close()

    def startZeroAir(self):
        # find out which serial port is connected
        ser = open_tca_port()
        ser.write('L1000')
        ser.write('E0000')
        ser.write('V1000')
        ser.write('U1000')
        ser.close()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    vis = Visualizer()

    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update)
    timer.start(vis.deltaT*1000)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
