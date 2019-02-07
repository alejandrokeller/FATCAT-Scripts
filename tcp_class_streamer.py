#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import socket
import sys
import ast # for datastring parsing
import numpy as np

from collections import namedtuple

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
        self.server_address = ('localhost', 10000)
        print >>sys.stderr, 'starting up on %s port %s' % self.server_address
        self.sock.bind(self.server_address) # Bind the socket to the port
        self.sock.listen(1) # Listen for incoming connections
        print >>sys.stderr, 'waiting for a connection'
        self.connection, self.client_address = self.sock.accept() # Wait for a connection
        print >>sys.stderr, 'connection from', self.client_address

        # init pyqt
        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title="TC Analyzer")
        self.win.showFullScreen()
        self.win.setWindowTitle('TC Analyzer')
        pg.setConfigOptions(antialias=False)
        pg.setConfigOption('foreground', 'w')

        #init data structure
        self.numSamples = 600 
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

        self.streamVarsData = self.tcaData._make(np.zeros((np.shape(self.keys)[0],self.numSamples)))

        # setup plots
        self.deltaT = 1 # s, sampling time
        self.pen = pg.mkPen('y', width=1)
        self.t = np.linspace(-self.deltaT*self.numSamples, 0, self.numSamples)

        self.Tcurves = dict()

        self.Tplot = self.win.addPlot(row=0, col=0, rowspan=2, title="")
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

        self.Pplot = self.win.addPlot(row=3, col=0, title="")
        self.Pplot.setRange(yRange=[50, 100])
        self.Pplot.setLabel('left', "CO2 Press.", units='kPa')
        self.Pplot.setLabel('bottom', "t", units='s')
        self.Pplot.showGrid(False, True)
        self.Pcurves[0] = self.Pplot.plot(self.t, self.streamVarsData.pco2, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Ccurves = dict()

        self.Cplot = self.win.addPlot(row=2, col=0, title="")
#        self.Cplot.setRange(yRange=[0, 100])
        self.Cplot.setLabel('left', "CO2", units='ppm')
        self.Cplot.setLabel('bottom', "t", units='s')
        self.Cplot.showGrid(False, True)
        self.Ccurves[0] = self.Cplot.plot(self.t, self.streamVarsData.co2, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

        self.Fcurves = dict()

        self.Fplot = self.win.addPlot(row=4, col=0, title="")
#        self.Fplot.setRange(yRange=[0, 100])
        self.Fplot.setLabel('left', "Flow", units='lpm')
        self.Fplot.setLabel('bottom', "t", units='s')
        self.Fplot.showGrid(False, True)
        self.Fcurves[0] = self.Fplot.plot(self.t, self.streamVarsData.flow, pen=pg.mkPen('y', width=1))
#        self.win.nextRow()

    def update(self):

        try: 
            self.datastring = self.connection.recv(1024)

            if self.datastring:
                self.daytime, self.datastring = self.datastring.split('\t', 1)
                self.datavector = [ast.literal_eval(s) for s in self.datastring.split( )]
                i = 0
                for k in self.keys:
                    self.tempArray = np.roll(self.streamVarsData[i], -1)
                    self.tempArray[-1] = self.datavector[i]
                    self.streamVarsData = self.streamVarsData._replace(**{k:self.tempArray})
                    i += 1
                print >>sys.stderr, self.streamVarsData.runtime
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
                
        except Exception as e:
            print >>sys.stderr, e
##            raise
                

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    vis = Visualizer()

    timer = QtCore.QTimer()
    timer.timeout.connect(vis.update)
    timer.start(1000)

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
