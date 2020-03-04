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
###        self.win = pg.GraphicsWindow(title="OCU")
###        self.win.showFullScreen()
###        self.win.setWindowTitle('OCU Control Panel')
        pg.setConfigOptions(antialias=False)
        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.datastring = ""
        self.graphLength = 600 # seconds
        self.deltaT = 0.5 # s, sampling time
        self.numSamples = int(self.graphLength/self.deltaT)
        self.photodiode_constant = 0.04545 # nA/mV
        # set status to new application
        self.firstLoop = True

        self.keys = [
            "runtime",
            "svoc1",
            "voc1",
            "base1", # 20.9.2019 baseline VOC1
            "svoc2",
            "voc2",
            "base2", # 20.9.2019 baseline VOC1
            "mfc1",
            "mfc2",
            "flow1",
            "flow2",
            "tuv",
            "iuv",
            "inrH", # 20.9.2019 baseline VOC1
            "inT", # 20.9.2019 baseline VOC1
            "stvoc",
            "tvoc",
            "sinrH",
            "tbath",
            "status",
            "lamps"
            ]
        self.functions = [
            float,  # runtime
            int,    # svoc1
            float,  # voc1
            float,  # base1
            int,    # svoc2
            float,  # voc2
            float,  # base2
            float,  # mfc1
            float,  # mfc2
            float,  # flow1
            float,  # flow2
            float,  # tuv
            float,  # iuv
            float,  # inrH
            float,  # inT
            int,     # stvoc
            float,   # tvoc
            int,     # sinrH
            float,   # tbath
            hex2bin, # status
            hex2bin  # lamps
            ]
        
        self.units = [
            's',    # runtime
            'mV',   # svoc1
            'mV',   # voc1
            'mV',   # base1
            'mV',   # svoc2
            'mV',   # voc2
            'mV',   # base2
            'ml',   # mfc1
            'ml',   # mfc2
            'slpm', # flow1
            'slpm', # flow2
            'degC', # tuv
            'mv',   # iuv
            '%',    # inrH
            'degC', # inT
            'degC', # stvoc
            'degC', # tvoc
            'degC', # sinrH
            'degC', # tbath
            '-',    # status
            '-'     # lamps
            ]

        self.unitsDict = dict(zip(self.keys, self.units))
        self.df = pd.DataFrame(columns=self.keys)
        zeroDict = dict(zip(self.keys,
                       map(partial(apply, a="0"), self.functions)
                       ))
        self.df = self.df.append([zeroDict]*self.numSamples,ignore_index=True)
            
        self.statusKeys = [
            "res4",
            "res3",
            "rH",
            "tube_heat",
            "voc2",
            "voc1",
            "pump2",
            "pump1"]

        self.lampKeys = [
            "run_flag",
            "reslamp1",
            "reslamp2",
            "lamp4",
            "lamp3",
            "lamp2",
            "lamp1",
            "lamp0"
            ]

        self.lampString = '00000'
        
        self.statusDict = {}
        for k in self.statusKeys:
            self.statusDict[k] = 0

        self.lampDict = {}
        for k in self.lampKeys:
            self.lampDict[k] = 0

        # setup plots
        self.pen = pg.mkPen('y', width=1)
        self.t = np.linspace(-self.graphLength, 0, self.numSamples)

        self.PIDcurves = dict()

        self.PIDplot = pg.PlotWidget()
        self.PIDplot.addLegend()
        #self.PIDplot.setRange(yRange=[0, 900])
        self.PIDplot.setLabel('left', "PID voltage", units='mV')
        self.PIDplot.setLabel('bottom', "t", units='s')
        self.PIDplot.showGrid(False, True)
        self.PIDcurves[0] = self.PIDplot.plot(self.t, self.df['svoc1'], pen=pg.mkPen('y', width=1, style=QtCore.Qt.DashLine))
        self.PIDcurves[1] = self.PIDplot.plot(self.t, self.df['voc1'], pen=pg.mkPen('y', width=1), name='PID1')
        self.PIDcurves[2] = self.PIDplot.plot(self.t, self.df['svoc2'], pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))
        self.PIDcurves[3] = self.PIDplot.plot(self.t, self.df['voc2'], pen=pg.mkPen('r', width=1), name='PID2')
        
        self.Fcurves = dict()

        self.Fplot = pg.PlotWidget()
        self.Fplot.addLegend()
        self.Fplot.setRange(yRange=[-0.005, 0.105])
        self.Fplot.setLabel('left', "VOC Flow", units='lpm')
        self.Fplot.setLabel('bottom', "t", units='s')
        self.Fplot.showGrid(False, True)
        self.Fcurves[0] = self.Fplot.plot(self.t, self.df['mfc1'], pen=pg.mkPen('y', width=1), name='MFC1')
        self.Fcurves[1] = self.Fplot.plot(self.t, self.df['mfc2'], pen=pg.mkPen('r', width=1), name='MFC2')
        # currently the set variable does not exists
        #self.Fcurves[3] = self.Fplot.plot(self.t, self.df['smfc2'], pen=pg.mkPen('r', width=1, style=QtCore.Qt.DashLine))

#####################################################################

        ## Define a top level widget to hold the controls
        self.widgets = QtGui.QWidget()
        self.widgets.setWindowTitle("OCU: Organics Coating Unit")
        self.widgets.showFullScreen()

        ## Create infotext widgets to be placed inside
        self.lblLamp      = QtGui.QLabel("Lamps")
        self.lblVOCTctr   = QtGui.QLabel("VOC heater")
        self.lblBath      = QtGui.QLabel("rH:")
        self.lblBathrH    = QtGui.QLabel("")
        self.lblTube      = QtGui.QLabel("VOC:")
        self.lblTubeT     = QtGui.QLabel("")
        self.lblVOC1      = QtGui.QLabel("VOC1 ()")
        self.lblVOC2      = QtGui.QLabel("VOC2 ()")
        self.lblPump1     = QtGui.QLabel("Pump1")
        self.lblPump2     = QtGui.QLabel("Pump2")
        self.lblLamps     = QtGui.QLabel("OFR:")
        self.lblLampsData = QtGui.QLabel("")
        # added 20.9.2019
        self.lblInlet     = QtGui.QLabel("Inlet:")
        self.lblInletData = QtGui.QLabel("")
        
        self.lblCD        = QtGui.QLabel("0")

        ## Create button widgets for actions
        button_size  = 27
        self.btnLamp      = QtGui.QPushButton("")            # Turn lamps on or off
        self.btnLamp.setFixedWidth(button_size)
        self.btnLamp.setFixedHeight(button_size)
        self.btnVOCTctr   = QtGui.QPushButton("")            # Turn VOC heater on or off
        self.btnVOCTctr.setFixedHeight(button_size)
        self.btnVOCTctr.setFixedWidth(button_size)
        self.btnBath      = QtGui.QPushButton("")            # Turn rH control on/off
        self.btnBath.setFixedWidth(button_size)
        self.btnBath.setFixedHeight(button_size)
        self.btnTube      = QtGui.QPushButton("")             # Turn Tube Heating on/off
        self.btnTube.setFixedWidth(button_size)
        self.btnTube.setFixedHeight(button_size)
        self.btnVOC1      = QtGui.QPushButton("")             # TURN VOC1 control on/off
        self.btnVOC1.setFixedWidth(button_size)
        self.btnVOC1.setFixedHeight(button_size)
        self.btnVOC2      = QtGui.QPushButton("")            # TURN VOC2 control on/off
        self.btnVOC2.setFixedWidth(button_size)
        self.btnVOC2.setFixedHeight(button_size)
        self.btnPump1     = QtGui.QPushButton("")            # Turn pump 1 on/off
        self.btnPump1.setFixedWidth(button_size)
        self.btnPump1.setFixedHeight(button_size)
        self.btnPump2     = QtGui.QPushButton("")            # Turn pump 2 on/off
        self.btnPump2.setFixedWidth(button_size)
        self.btnPump2.setFixedHeight(button_size)

        self.btnLamp.clicked.connect(self.toggleAllLamps)
        self.btnVOCTctr.clicked.connect(self.toggleVOCHeater)
        self.btnVOC1.clicked.connect(self.toggleVOC1)
        self.btnVOC2.clicked.connect(self.toggleVOC2)
        self.btnPump1.clicked.connect(self.togglePump1)
        self.btnPump2.clicked.connect(self.togglePump2)
        self.btnBath.clicked.connect(self.togglerH)

        ## Create widgets for controlling MFC2
        self.btnMFC2      = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnMFC2.setFixedWidth(button_size)
        self.btnMFC2.setFixedHeight(button_size)
        self.btnMFC2.clicked.connect(self.setMFC2)
        self.lblMFC2      = QtGui.QLabel("MFC2 (mlpm):")
        self.spMFC2       = QtGui.QSpinBox()
        self.spMFC2.setRange(0,100)

        ## Create widgets for controlling VOC1
        self.btnSVOC1      = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnSVOC1.setFixedWidth(button_size)
        self.btnSVOC1.setFixedHeight(button_size)
        self.btnSVOC1.clicked.connect(self.setSVOC1)
        self.lblSVOC1      = QtGui.QLabel("VOC1 (mV):")
        self.spSVOC1       = QtGui.QSpinBox()
        self.spSVOC1.setRange(0,2500)

        ## Create widgets for controlling VOC Heater
        self.btnVOCT       = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnVOCT.setFixedWidth(button_size)
        self.btnVOCT.setFixedHeight(button_size)
        self.btnVOCT.clicked.connect(self.setVOCT)
        self.lblVOCT       = QtGui.QLabel("VOC (degC):")
        self.spVOCT        = QtGui.QSpinBox()
        self.spVOCT.setRange(0,80)

        ## Create widgets for serial commands
        self.btnSERIAL     = QtGui.QPushButton(">>")  # Sends new MFC2 flow
        self.btnSERIAL.setFixedWidth(button_size)
        self.btnSERIAL.setFixedHeight(button_size)
        self.btnSERIAL.clicked.connect(self.sendSerialCMD)
        self.lblSERIAL     = QtGui.QLabel("Command:")
        self.lineSERIAL    = QtGui.QLineEdit()
        validator = QtGui.QRegExpValidator(QtCore.QRegExp("[abFpirRXZ][0-9]{4}"))
        self.lineSERIAL.setValidator(validator)

        ## Create a grid layout to manage the controls size and position
        self.controlsLayout = QtGui.QGridLayout()
        self.encloserLayout = QtGui.QVBoxLayout()
        self.lampsButtonsLayout = QtGui.QHBoxLayout()
        self.mfcLayout = QtGui.QGridLayout()
        self.encloserLayout.addLayout(self.controlsLayout)
        self.encloserLayout.addLayout(self.lampsButtonsLayout)
        self.encloserLayout.addLayout(self.mfcLayout)
        self.encloserLayout.addStretch(1)

        ## Create individual lamp buttons
        self.lamps = []
        for i in range(5):
            self.lamps.append(i)
            self.lamps[i] = QtGui.QPushButton("L{}".format(i))
            self.lamps[i].setFixedWidth(1.2*button_size)
            self.lamps[i].setFixedHeight(button_size)
            self.lamps[i].clicked.connect(partial(self.toggleLamp,i))
            self.lampsButtonsLayout.addWidget(self.lamps[i])

        ## Add widgets to the layout in their proper positions
        self.controlsLayout.addWidget(self.lblLamp,      0, 1)
        self.controlsLayout.addWidget(self.lblVOCTctr,   1, 1)
        self.controlsLayout.addWidget(self.lblVOC1,      2, 1)
        self.controlsLayout.addWidget(self.lblVOC2,      3, 1)
        self.controlsLayout.addWidget(self.lblPump1,     4, 1)
        self.controlsLayout.addWidget(self.lblPump2,     5, 1)
        #self.controlsLayout.addWidget(self.lblBath,      6, 0)
        self.controlsLayout.addWidget(self.lblBathrH,    6, 1)
        #self.controlsLayout.addWidget(self.lblTube,      7, 0)
        #self.controlsLayout.addWidget(self.lblTubeT,     7, 1)
        #self.controlsLayout.addWidget(self.lblLamps,     8, 0)
        #self.controlsLayout.addWidget(self.lblLampsData, 8, 1)
        #self.controlsLayout.addWidget(self.lblInlet,     9, 0)
        #self.controlsLayout.addWidget(self.lblInletData, 9, 1)

##        self.controlsLayout.addWidget(self.lblCD,    9, 0, 1, 2) # example of two spaces horizontal (one vertical)

        self.controlsLayout.addWidget(self.btnLamp,     0, 0)
        self.controlsLayout.addWidget(self.btnVOCTctr,  1, 0)
        self.controlsLayout.addWidget(self.btnVOC1,     2, 0)
        self.controlsLayout.addWidget(self.btnVOC2,     3, 0)
        self.controlsLayout.addWidget(self.btnPump1,    4, 0)
        self.controlsLayout.addWidget(self.btnPump2,    5, 0)
        self.controlsLayout.addWidget(self.btnBath,     6, 0)

        ## Add Widgets to the MFCLayout
        self.mfcLayout.addWidget(self.lblSVOC1,    0, 0)
        self.mfcLayout.addWidget(self.spSVOC1,     0, 1)
        self.mfcLayout.addWidget(self.btnSVOC1,    0, 2)
        self.mfcLayout.addWidget(self.lblVOCT,     1, 0)
        self.mfcLayout.addWidget(self.spVOCT,      1, 1)
        self.mfcLayout.addWidget(self.btnVOCT,     1, 2)
        self.mfcLayout.addWidget(self.lblMFC2,     2, 0)
        self.mfcLayout.addWidget(self.spMFC2,      2, 1)
        self.mfcLayout.addWidget(self.btnMFC2,     2, 2)
        self.mfcLayout.addWidget(self.lblSERIAL,   3, 0)
        self.mfcLayout.addWidget(self.lineSERIAL,  3, 1)
        self.mfcLayout.addWidget(self.btnSERIAL,   3, 2)

        ## Create a QVBox layout to manage the plots
        self.plotLayout = QtGui.QVBoxLayout()

        ## Create a QHBox for the text info
        self.textLayout = QtGui.QHBoxLayout()
#        self.textLayout.addWidget(self.lblTube)
        self.textLayout.addWidget(self.lblTubeT)
#        self.textLayout.addWidget(self.lblLamps)
        self.textLayout.addWidget(self.lblLampsData)
#        self.textLayout.addWidget(self.lblInlet)
        self.textLayout.addWidget(self.lblInletData)
        self.plotLayout.addLayout(self.textLayout)

        self.plotLayout.addWidget(self.PIDplot)
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
                for k, j in zip(self.statusKeys, range(len(self.statusKeys))):
                    self.statusDict[k] = int(statusbyte[j])

                statusbyte = newData['lamps']
                self.lampString = ''
                for k, j in zip(self.lampKeys, range(len(self.lampKeys))):
                    self.lampDict[k] = int(statusbyte[j])
                    if j > 2:
                        ## LampString has the most significant bit to the left
                        self.lampString = self.lampString + statusbyte[j]

                if self.statusDict['voc1']:
                    self.PIDcurves[0].setData(self.t, self.df['svoc1'])
                    self.PIDcurves[1].setData(self.t, self.df['voc1'])
                else:
                    self.PIDcurves[0].clear()
                    self.PIDcurves[1].clear()

                if self.statusDict['voc2']:
                    self.PIDcurves[2].clear()
                    #self.PIDcurves[2].setData(self.t, self.df['svoc2'])
                    self.PIDcurves[3].setData(self.t, self.df['voc2'])
                else:
                    self.PIDcurves[2].clear()
                    self.PIDcurves[3].clear()

                # Data is received in mlpm. Dividing through 1000 to use pyqugraph autolabeling
                self.Fcurves[0].setData(self.t, self.df['mfc1']/1000)
                self.Fcurves[1].setData(self.t, self.df['mfc2']/1000)
                
####################################################################

                self.lblBathrH.setText("".join((str(int(newData['inrH'])), "/",
                                               str(newData['sinrH']), " %rH")))
                self.lblTubeT.setText("".join(("VOC: ", str(int(newData['tvoc'])), "/",
                                               str(newData['stvoc']), " degC")))
                self.lblLampsData.setText("".join(("ORF: ",str(int(newData['tuv'])), " degC, ",
                                                   str(int(newData['iuv']*self.device.uv_constant/1000)), " uA" )))
                self.lblInletData.setText("".join(("Inlet: ",str(int(newData['inT'])), " degC, ",
                                                   str(int(newData['inrH'])), "% rH" )))
                self.lblPump1.setText("".join(("Pump1 (", "{:.1f}".format(newData['flow1']), " slpm)")))
                self.lblPump2.setText("".join(("Pump2 (", "{:.1f}".format(newData['flow2']), " slpm)")))
                self.lblVOC1.setText("".join(("VOC1: ",str(int(newData['voc1'])), "/",
                                               str(newData['svoc1']), " mV")))
                self.lblVOC2.setText("".join(("VOC2: ",str(int(newData['voc2'])), " mV")))
                #self.lblMFC2.setText("".join(("MFC2: ",str(int(newData['mfc2'])), " mlpm")))

                # Initialize some indicators
                if self.firstLoop:
                    self.firstLoop = False
                    self.spMFC2.setValue(int(newData['mfc2']))
                    self.spSVOC1.setValue(int(newData['svoc1']))
                    self.spVOCT.setValue(int(newData['stvoc']))
                    

################# Example of color toggle
##                if (newData['countdown'] % 2 == 0):
##                    self.lblCD.setStyleSheet('color: black')
##                else:
##                    self.lblCD.setStyleSheet('color: red')
                
                if (self.lampDict['lamp0'] or self.lampDict['lamp1'] or self.lampDict['lamp2'] or
                    self.lampDict['lamp3'] or self.lampDict['lamp4']):
                    self.lblLamp.setStyleSheet('color: green')
                    self.lamps_status = True
                else:
                    self.lblLamp.setStyleSheet('color: red')
                    self.lamps_status = False

                for status, btn in zip(self.lampString[::-1], self.lamps):
                    if int(status) > 0:
                        btn.setStyleSheet("background-color: green")
                    else:
                        btn.setStyleSheet("background-color: red")

                if self.statusDict['voc1']:
                    self.lblVOC1.setStyleSheet('color: green')
                else:
                    self.lblVOC1.setStyleSheet('color: red')

                if self.statusDict['voc2']:
                    self.lblVOC2.setStyleSheet('color: green')
                else:
                    self.lblVOC2.setStyleSheet('color: red')

                if self.statusDict['tube_heat']:
                    self.lblVOCTctr.setStyleSheet('color: green')
                else:
                    self.lblVOCTctr.setStyleSheet('color: red')

                if self.statusDict['pump1']:
                    self.lblPump1.setStyleSheet('color: green')
                else:
                    self.lblPump1.setStyleSheet('color: red')

                if self.statusDict['pump2']:
                    self.lblPump2.setStyleSheet('color: green')
                else:
                    self.lblPump2.setStyleSheet('color: red')
                                    
        except Exception as e:
            print >>sys.stderr, e
##            raise

    def sendSerialCMD(self):
        commands = [self.lineSERIAL.text().encode("ascii")]
        print >> sys.stderr, commands
        self.device.send_commands(commands, open_port = True)
        self.lineSERIAL.clear()

    def setMFC2(self):
        self.device.set_mfc2(self.spMFC2.value() ,open_port = True)

    def setSVOC1(self):
        self.device.set_voc1(self.spSVOC1.value() ,open_port = True)

    def setVOCT(self):
        self.device.set_tubeT(self.spVOCT.value() ,open_port = True)
            
    def toggleAllLamps(self):
        if self.lamps_status:
            self.device.set_lamps('00000', open_port = True)
        else:
            self.device.set_lamps('11111', open_port = True)

    def toggleLamp(self, lamp):
        print "Old Lamp String: " + self.lampString[::-1]
        ## Reverse the string to change lamps according to GUI
        reverseString = self.lampString[::-1]
        new_value = str(int(reverseString[lamp]) ^ 1)
        s = list(reverseString)
        s[lamp] = new_value
        ## Join and reverse new string for compatibility with firmware
        new_string = ("".join(s))[::-1]
        print "New lamp String: " + new_string[::-1]
        self.device.set_lamps(new_string, open_port = True)

    def toggleVOCHeater(self):
        if self.statusDict['tube_heat']:
            commands = [self.device.tube_off_str]
        else:
            commands = [self.device.tube_on_str]
        self.device.send_commands(commands, open_port = True)
        
    def toggleVOC1(self):
        if self.statusDict['voc1']:
            commands = [self.device.voc1_off_str]
        else:
            commands = [self.device.voc1_on_str]
        self.device.send_commands(commands, open_port = True)

    def toggleVOC2(self):
        if self.statusDict['voc2']:
            commands = [self.device.voc2_off_str]
        else:
            commands = [self.device.voc2_on_str]
        self.device.send_commands(commands, open_port = True)

    def togglePump1(self):
        if self.statusDict['pump1']:
            commands = [self.device.pump1_off_str]
        else:
            commands = [self.device.pump1_on_str]
        self.device.send_commands(commands, open_port = True)

    def togglePump2(self):
        if self.statusDict['pump2']:
            commands = [self.device.pump2_off_str]
        else:
            commands = [self.device.pump2_on_str]
        self.device.send_commands(commands, open_port = True)
        
    def self.togglerH(self):
        if self.statusDict['rH']:
            commands = [self.device.rH_off_str]
        else:
            commands = [self.device.rH_on_str]
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
