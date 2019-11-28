#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# listens to a TCP broadcast and displays data using Ppyqt widgets
# provides also a buttons interface for interacting with the 
# measurement instrument

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import socket
import sys, os
import ast # for datastring parsing
import numpy as np
import configparser
from functools import partial # function mapping
from collections import namedtuple

import pandas as pd

import time
import serial
import serial.tools.list_ports

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(base_path + '/extras/')
from instrument import instrument

def hex2bin(s):
    hex_table = ['0000', '0001', '0010', '0011',
                 '0100', '0101', '0110', '0111',
                 '1000', '1001', '1010', '1011',
                 '1100', '1101', '1110', '1111']
    bits = ''
    for i in range(len(s)):
        bits += hex_table[int(s[i], base=16)]
    return bits

### map function for propper parameter convertion
def apply(f,a):
    return f(a)

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
    def __init__(self, host_name='localhost', host_port=10000, config_file='config.ini'):
        
        # init socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
        self.server_address = (host_name, host_port)
        print >>sys.stderr, 'starting up on %s port %s' % self.server_address
        self.sock.bind(self.server_address) # Bind the socket to the port
        self.sock.listen(1) # Listen for incoming connections
        print >>sys.stderr, 'waiting for a connection'
        self.connection, self.client_address = self.sock.accept() # Wait for a connection
        print >>sys.stderr, 'connection from', self.client_address

        self.device = instrument(config_file = config_file)

        # init pyqt
        self.app = QtGui.QApplication([])
###        self.win = pg.GraphicsWindow(title="TC Analyzer")
###        self.win.showFullScreen()
###        self.win.setWindowTitle('TC Analyzer')
        pg.setConfigOptions(antialias=False)
        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.numSamples = 1200
        self.datastring = ""
        self.deltaT = 0.5 # s, sampling time
        # set status to new application
        self.firstLoop = True

        self.keys = [
            "runtime",
            "spoven",
            "toven",
            "spcoil",
            "tcoil",
            "spband",
            "tband",
            "eflow",
            "tcat",
            "tco2",
            "pco2",
            "co2",
            "flow",
            "curr",
            "countdown",
            "status",
            "co2abs",
            "h2o",
            "h2oabs",
            "rawco2",
            "rawco2ref",
            "rawh2o",
            "rawh2oref"
            ]
        self.functions = [
            float,  # runtime
            int,    # spoven
            float,  # toven
            int,    # spcoil
            float,  # tcoil
            int,    # spband
            float,  # tband
            float,  # eflow
            float,  # tcat
            float,  # tco2
            float,  # pco2
            float,  # co2
            float,  # flow
            float,  # current
            int,    # countdown
            hex2bin,# status
            float,  # co2abs
            float,  # h2o
            float,  # h2oabs
            int,    # rawco2
            int,    # rawco2ref
            int,    # rawh2o
            int     # rawh2oref
            ]
        
        self.units = [
            "s",        # runtime
            "°C",       # spoven
            "°C",       # toven
            "°C",       # spcoil
            "°C",       # tcoil
            "°C",       # spband
            "°C",       # tband
            "lpm",      # eflow
            "°C",       # tcat
            "°C",       # tco2
            "kPa",      # pco2
            "ppm",      # co2
            "lpm",      # flow
            "A",        # current
            "S",        # countdown
            "-",        # status
            "- [absorption]",   # co2abs
            "mmol/mol", # h2o
            "- [absorption]",   # h2oabs
            "- [raw]",  # rawco2
            "- [raw]",  # rawco2ref
            "- [raw]",  # rawh2o
            "- [raw]"   # rawh2oref
            ]

        self.unitsDict = dict(zip(self.keys, self.units))
        self.df = pd.DataFrame(columns=self.keys)
        zeroDict = dict(zip(self.keys,
                       map(partial(apply, a="0"), self.functions)
                       ))
        self.df = self.df.append([zeroDict]*self.numSamples,ignore_index=True)
            
        self.statusKeys = [
            "valve",
            "pump",
            "fan",
            "oven",
            "band",
            "licor",
            "res2",
            "res"]
        
#        self.statusData = namedtuple("statusData", self.statusKeys)
#        self.statusVarsData = self.statusData._make(np.zeros((np.shape(self.statusKeys)[0],self.numSamples)))
        
#        self.statusDf = pd.DataFrame(np.zeros(shape = (self.numSamples,len(self.statusKeys))), columns = self.statusKeys)
        self.statusDict = {}
        for k in self.statusKeys:
            self.statusDict[k] = 0

        # setup plots
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
        self.Tcurves[0] = self.Tplot.plot(self.t, self.df['spoven'], pen=pg.mkPen('y', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[1] = self.Tplot.plot(self.t, self.df['toven'], pen=pg.mkPen('y', width=1), name='Oven')
        self.Tcurves[2] = self.Tplot.plot(self.t, self.df['spcoil'], pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[3] = self.Tplot.plot(self.t, self.df['tcoil'], pen=pg.mkPen('r', width=1), name='Coil')
        self.Tcurves[4] = self.Tplot.plot(self.t, self.df['spband'], pen=pg.mkPen('b', width=1, style=QtCore.Qt.DashLine))
        self.Tcurves[5] = self.Tplot.plot(self.t, self.df['tband'], pen=pg.mkPen('b', width=1), name='Band')
        self.Tcurves[6] = self.Tplot.plot(self.t, self.df['tcat'], pen=pg.mkPen('g', width=1), name='Cat')
#        self.win.nextRow()

        self.Pcurves = dict()

###        self.Pplot = self.win.addPlot(row=3, col=0, title="")
        self.Pplot = pg.PlotWidget()
        self.Pplot.setRange(yRange=[50, 100])
        self.Pplot.setLabel('left', "CO2 Press.", units='kPa')
        self.Pplot.setLabel('bottom', "t", units='s')
        self.Pplot.showGrid(False, True)
        self.Pcurves[0] = self.Pplot.plot(self.t, self.df['pco2'], pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Ccurves = dict()

###        self.Cplot = self.win.addPlot(row=2, col=0, title="")
        self.Cplot = pg.PlotWidget()
#        self.Cplot.setRange(yRange=[0, 100])
        self.Cplot.setLabel('left', "CO2", units='ppm')
        self.Cplot.setLabel('bottom', "t", units='s')
        self.Cplot.showGrid(False, True)
        self.Ccurves[0] = self.Cplot.plot(self.t, self.df['co2'], pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Fcurves = dict()

###        self.Fplot = self.win.addPlot(row=4, col=0, title="")
        self.Fplot = pg.PlotWidget()
        self.Fplot.addLegend()
        self.Fplot.setRange(yRange=[0, 10])
        self.Fplot.setLabel('left', "Flow", units='lpm')
        self.Fplot.setLabel('bottom', "t", units='s')
        self.Fplot.showGrid(False, True)
        self.Fcurves[0] = self.Fplot.plot(self.t, self.df['flow'], pen=pg.mkPen('y', width=1), name='Intern')
        self.Fcurves[1] = self.Fplot.plot(self.t, self.df['flow'], pen=pg.mkPen('r', width=1), name='Extern')
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
        self.lblESample   = QtGui.QLabel("Sample (int. pump on)")
        self.lblEAnalysis = QtGui.QLabel("Zero Air +bypass")
        
        self.lblCD        = QtGui.QLabel("0")

        self.lblLicorT    = QtGui.QLabel("CO2: ")
        self.lblLicorH2O  = QtGui.QLabel("H2O: ")


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
        self.btnESample   = QtGui.QPushButton("")            # activate emissions sampling mode
        self.btnESample.setFixedWidth(self.button_size)
        self.btnEAnalysis = QtGui.QPushButton("")            # prepare for emissions analisys
        self.btnEAnalysis.setFixedWidth(self.button_size)

        self.btnPump.clicked.connect(self.togglePump)
        self.btnBand.clicked.connect(self.toggleBand)
        self.btnValve.clicked.connect(self.toggleValve)
        self.btnLicor.clicked.connect(self.toggleLicor)
        self.btnOven.clicked.connect(self.toggleOven)
        self.btnRes2.clicked.connect(self.toggleRes2)
        self.btnSample.clicked.connect(self.startSample)
        self.btnZeroAir.clicked.connect(self.startZeroAir)
        self.btnESample.clicked.connect(self.SampleEmissions)
        self.btnEAnalysis.clicked.connect(self.AnalizeEmissions)

        ## Create widgets for controlling Internal MFC
        self.btnMFC1      = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnMFC1.setFixedWidth(self.button_size)
        self.btnMFC1.setFixedHeight(self.button_size)
        self.btnMFC1.clicked.connect(self.setMFC1)
        self.lblMFC1      = QtGui.QLabel("Pump (dlpm):")
        self.spMFC1       = QtGui.QSpinBox()
        self.spMFC1.setRange(0,20)
        
        ## Create widgets for controlling External MFC
        self.btnMFC2      = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnMFC2.setFixedWidth(self.button_size)
        self.btnMFC2.setFixedHeight(self.button_size)
        self.btnMFC2.clicked.connect(self.setMFC2)
        self.lblMFC2      = QtGui.QLabel("E. Pump (dlpm):")
        self.spMFC2       = QtGui.QSpinBox()
        self.spMFC2.setRange(0,170)

        ## Create a grid layout to manage the controls size and position
        self.controlsLayout = QtGui.QGridLayout()
        self.mfcLayout = QtGui.QGridLayout()
        self.encloserLayout = QtGui.QVBoxLayout()
        self.encloserLayout.addLayout(self.controlsLayout)
        self.encloserLayout.addLayout(self.mfcLayout)
        self.encloserLayout.addStretch(1)

        ## Add widgets to the layout in their proper positions
        self.controlsLayout.addWidget(self.lblPump,       0, 1)
        self.controlsLayout.addWidget(self.lblBand,       1, 1)
        self.controlsLayout.addWidget(self.lblOven,       2, 1)
        self.controlsLayout.addWidget(self.lblValve,      3, 1)
        self.controlsLayout.addWidget(self.lblLicor,      4, 1)
        self.controlsLayout.addWidget(self.lblRes2,       5, 1)
        self.controlsLayout.addWidget(self.lblFan,        7, 0)
        self.controlsLayout.addWidget(self.lblRes,        7, 1)
        self.controlsLayout.addWidget(self.lblSample,     9, 1)
        self.controlsLayout.addWidget(self.lblZeroAir,   10, 1)
        self.controlsLayout.addWidget(self.lblESample,   13, 1)
        self.controlsLayout.addWidget(self.lblEAnalysis, 14, 1)

        self.controlsLayout.addWidget(self.lblCD,        8, 0, 1, 2)

        self.controlsLayout.addWidget(self.lblLicorT,   11, 0, 1, 2)
        self.controlsLayout.addWidget(self.lblLicorH2O, 12, 0, 1, 2)

        self.controlsLayout.addWidget(self.btnPump,       0, 0)
        self.controlsLayout.addWidget(self.btnBand,       1, 0)
        self.controlsLayout.addWidget(self.btnOven,       2, 0)
        self.controlsLayout.addWidget(self.btnValve,      3, 0)
        self.controlsLayout.addWidget(self.btnLicor,      4, 0)
        self.controlsLayout.addWidget(self.btnRes2,       5, 0)
        #self.controlsLayout.addWidget(self.btnOven,  7, 0, 1, 2)
        self.controlsLayout.addWidget(self.btnSample,     9, 0)
        self.controlsLayout.addWidget(self.btnZeroAir,   10, 0)
        self.controlsLayout.addWidget(self.btnESample,   13, 0)
        self.controlsLayout.addWidget(self.btnEAnalysis, 14, 0)

         ## Add Widgets to the MFCLayout
        self.mfcLayout.addWidget(self.lblMFC1,     0, 0)
        self.mfcLayout.addWidget(self.spMFC1,      0, 1)
        self.mfcLayout.addWidget(self.btnMFC1,     0, 2)
        self.mfcLayout.addWidget(self.lblMFC2,     1, 0)
        self.mfcLayout.addWidget(self.spMFC2,      1, 1)
        self.mfcLayout.addWidget(self.btnMFC2,     1, 2)
        #self.mfcLayout.addWidget(self.lblSERIAL,   2, 0)
        #self.mfcLayout.addWidget(self.lineSERIAL,  2, 1)
        #self.mfcLayout.addWidget(self.btnSERIAL,   2, 2)


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
                ####### syntax changed for the status byte... ignore
                ####### additional variables at the end
                
                ###### DATAFRAME version
                #Eliminate first element
                self.df = self.df[1:self.numSamples]
                values = self.datastring.split( )
                newData = self.df.iloc[[-1]].to_dict('records')[0]
                for k, f, v in zip(self.keys, self.functions, values):
                    try:
                        newData[k] = f(v)
                    except:
                        print "could not apply funtion " + str(f) + " to " + str(v)

                self.df = self.df.append([newData],ignore_index=True)

                statusbyte = newData['status']
                j = 0
                for k in self.statusKeys:
                    self.statusDict[k] = int(statusbyte[j])
                    j += 1
                
##                i = 0
##                self.datavector = []
##                for s in self.datastring.split( ):
####                    if i < len(self.keys):
##                    if i < 13:
##                         #### use this values als integers
##                         self.datavector.append(ast.literal_eval(s))
##                    else:
##                        try:
##                             #### transcode the last value from hex to a binary array
##                             self.statusbyte = hex2bin(s)
##                             j = 0
##                             #### now store it in the status variables
##                             for k in self.statusKeys:
##                                 self.tempArray = np.roll(self.statusVarsData[j], -1)
##                                 self.tempArray[-1] = int(self.statusbyte[j])                             
##                                 self.statusVarsData = self.statusVarsData._replace(**{k:self.tempArray})
##                                 j += 1
##                             break
##                        except:
##                            pass
##                    i += 1
##                    
##                i = 0
##                for k in self.keys:
##                    self.tempArray = np.roll(self.streamVarsData[i], -1)
##                    self.tempArray[-1] = self.datavector[i]
##                    self.streamVarsData = self.streamVarsData._replace(**{k:self.tempArray})
##                    i += 1
####                print >>sys.stderr, self.streamVarsData.runtime
                self.Tcurves[0].setData(self.t, self.df['spoven'])
                self.Tcurves[1].setData(self.t, self.df['toven'])
                self.Tcurves[2].setData(self.t, self.df['spcoil'])
                self.Tcurves[3].setData(self.t, self.df['tcoil'])
                self.Tcurves[4].setData(self.t, self.df['spband'])
                self.Tcurves[5].setData(self.t, self.df['tband'])
                self.Tcurves[6].setData(self.t, self.df['tcat'])

                self.Pcurves[0].setData(self.t, self.df['pco2'])

                self.Ccurves[0].setData(self.t, self.df['co2'])

                self.Fcurves[0].setData(self.t, self.df['flow'])
                self.Fcurves[1].setData(self.t, self.df['eflow'])
                
####################################################################

                self.lblCD.setText("Countdown: {:.0f} ({:.0f} A)".format(newData['countdown'], newData['curr']))
                self.lblOven.setText("Oven: {:.0f}/{:.0f} degC".format(newData['toven'], newData['spoven']))
                self.lblBand.setText("Band: {:.0f}/{:.0f} degC".format(newData['tband'], newData['spband']))
                self.lblPump.setText("Pump ({:.2f} lpm)".format(newData['flow']))
                self.lblRes2.setText("Ext. Pump ({:.1f} lpm)".format(newData['eflow']))

                self.lblLicorT.setText("CO2: {:.0f} ppm ({:.0f} degC)".format(newData['co2'], newData['tco2']))
                self.lblLicorH2O.setText("H2O: {:.1f} mmol/mol".format(newData['h2o']))

                # Initialize some indicators
                if self.firstLoop:
                    self.firstLoop = False
                    self.spMFC1.setValue(int(newData['flow']*10))
                    self.spMFC2.setValue(int(newData['eflow']*10))

                if (newData['countdown'] % 2 == 0):
                    self.lblCD.setStyleSheet('color: black')
                else:
                    self.lblCD.setStyleSheet('color: red')
                
                if self.statusDict['oven']:
                    self.lblOven.setStyleSheet('color: green')
                else:
                    self.lblOven.setStyleSheet('color: red')

                if self.statusDict['band']:
                    self.lblBand.setStyleSheet('color: green')
                else:
                    self.lblBand.setStyleSheet('color: red')

                if self.statusDict['fan']:
                    self.lblFan.setStyleSheet('color: green')
                else:
                    self.lblFan.setStyleSheet('color: red')

                if self.statusDict['pump']:
                    self.lblPump.setStyleSheet('color: green')
                else:
                    self.lblPump.setStyleSheet('color: red')

                if self.statusDict['licor']:
                    self.lblLicor.setStyleSheet('color: green')
                else:
                    self.lblLicor.setStyleSheet('color: red')

                if self.statusDict['valve']:
                    self.lblValve.setStyleSheet('color: green')
                else:
                    self.lblValve.setStyleSheet('color: red')

                if self.statusDict['res']:
                    self.lblRes.setStyleSheet('color: green')
                else:
                    self.lblRes.setStyleSheet('color: red')

                if self.statusDict['res2']:
                    self.lblRes2.setStyleSheet('color: green')
                else:
                    self.lblRes2.setStyleSheet('color: red')

                if (not self.statusDict['pump'] and not self.statusDict['valve'] and
                        self.statusDict['res2'] and not self.statusDict['licor']):
                    self.lblSample.setStyleSheet('color: green')
                else:
                    self.lblSample.setStyleSheet('color: red')

                if (self.statusDict['pump']     and self.statusDict['valve'] and
                    not self.statusDict['res2'] and self.statusDict['licor']):
                    self.lblZeroAir.setStyleSheet('color: green')
                else:
                    self.lblZeroAir.setStyleSheet('color: red')

                if (self.statusDict['pump'] and not self.statusDict['valve'] and
                        self.statusDict['res2'] and not self.statusDict['licor']):
                    self.lblESample.setStyleSheet('color: green')
                else:
                    self.lblESample.setStyleSheet('color: red')

                if (self.statusDict['pump']     and self.statusDict['valve'] and
                    self.statusDict['res2'] and self.statusDict['licor']):
                    self.lblEAnalysis.setStyleSheet('color: green')
                else:
                    self.lblEAnalysis.setStyleSheet('color: red')
                
        except Exception as e:
            print >>sys.stderr, e
##            raise

    def setMFC1(self):
        self.device.set_mfc1(self.spMFC1.value() ,open_port = True)

    def setMFC2(self):
        self.device.set_mfc2(self.spMFC2.value() ,open_port = True)

    def togglePump(self):
        if self.statusDict['pump']:
            commands = ['U0000']
        else:
            commands = ['U1000']
        self.device.send_commands(commands, open_port = True)

    def toggleBand(self):
        if self.statusDict['band']:
            commands = ['B0000']
        else:
            commands = ['B1000']
        self.device.send_commands(commands, open_port = True)

    def toggleValve(self):
        if self.statusDict['valve']:
            commands = ['V0000']
        else:
            commands = ['V1000']
        self.device.send_commands(commands, open_port = True)

    def toggleLicor(self):
        if self.statusDict['licor']:
            commands = ['L0000']
        else:
            commands = ['L1000']
        self.device.send_commands(commands, open_port = True)

    def toggleOven(self):
        if self.statusDict['oven']:
            commands = ['O0000']
        else:
            commands = ['O1000']
        self.device.send_commands(commands, open_port = True)

    def toggleRes2(self):
        if self.statusDict['res2']:
            commands = ['E0000']
        else:
            commands = ['E1000']
        self.device.send_commands(commands, open_port = True)

    def startSample(self):
        commands = ['U0000',
                    'V0000',
                    'E1000',
                    'L0000']
        self.device.send_commands(commands, open_port = True)

    def startZeroAir(self):
        commands = ['L1000',
                    'E0000',
                    'V1000',
                    'U1000']
        self.device.send_commands(commands, open_port = True)

    def SampleEmissions(self):
        c = 'C{0:04d}!'.format(self.spMFC2.value())
        commands = ['U1000', # internal pump on
                    c,       # set external flow rate 
                    'V0000', # sample goes through bypass
                    'E1000', # external pump on
                    'L0000'] # external valve off
        self.device.send_commands(commands, open_port = True)

    def AnalizeEmissions(self):
        c = 'C{0:04d}!'.format(self.spMFC2.value()+self.spMFC1.value())
        commands = ['L1000', # external valve on
                    'E1000', # external pump on
                    c,       # increment external flow rate
                    'V1000', # sample goes to instrument filter
                    'U1000'] # internal pump on
        self.device.send_commands(commands, open_port = True)

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    # READ ini file
    config_file = base_path + '/config.ini'
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        host_name = eval(config['TCP_INTERFACE']['HOST_NAME'])
        host_port = eval(config['TCP_INTERFACE']['HOST_PORT'])
    else:
        print >> sys.stderr, "Could not find the configuration file: " + config_file
        exit()


    vis = Visualizer(host_name=host_name, host_port=host_port, config_file=config_file)

    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update)
    timer.start(vis.deltaT*1000)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
