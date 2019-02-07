#!/usr/bin/env python

import argparse        # for argument parsing
import os, sys
import ast             # for datastring parsing
from collections import namedtuple
import numpy as np
import time            # required by the uploadData function
from fatcat_uploader import Uploader # httpsend command for uploading data
#import math
#from scipy.integrate import simps

ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm

def simplecount(fh):
    lines = 0
    for line in fh:
        lines += 1
    return lines

class EventError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Datafile(object):
    def __init__(self, datafile): # datafile is a valid filepointer

        #init data structure
        self.datastring = ""
        self.datafile = datafile.name
        self.csvfile = datafile

        self.numSamples, events = self.countAndFetchEvents()
        self.numEvents  = len(events)

        self.eventDaytime = []
        self.fileDaytime = [None] * self.numSamples

        self.eventKeys = [
            "index",
            "runtime",
            "baseline",
            "maxtoven",
            "tc"]
        self.eventResult = namedtuple("results", self.eventKeys)
        self.results     = self.eventResult._make(np.zeros(
                           (np.shape(self.eventKeys)[0],self.numEvents)))
        self.results     = self.results._replace(**{"index":events})
#        print >>sys.stderr, '{0} lines counted.\nEvent(s) found {1}'.format(self.numSamples, self.results.index)

        self.baselinelength    =   5 # time for baseline calculation in seconds
        self.integrationlength = 330 # length of integration in seconds

        self.filekeys = [
        #    "daytime",
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

        self.keys = [
        #    "daytime",
            "runtime",
        #    "spoven",
            "toven",
        #    "spcoil",
        #    "tcoil",
        #    "spband",
        #    "tband",
        #    "spcat",
        #    "tcat",
        #    "tco2",
            "pco2",
            "co2",
            "flow",
        #    "curr",
            "countdown"]

        self.uploadKeys = [
            "date",
            "time",
            "datafile",
            "dataindex",
            "runtime",
            "co2base",
            "tempoven",
            "tc"]

        # generates a key map from (all) the datafile to the reduced list used here
        self.keymap = []
        for k in self.keys:
            self.keymap.append(self.filekeys.index(k))

        self.tcaData = namedtuple("tcaData", self.keys)
        self.fileData = self.tcaData._make(np.zeros((np.shape(self.keys)[0],
                        self.numSamples)))

#        self.load()
#        self.findEvents()
#        self.loadEventsData()
#        self.calculateAllBaseline()
#        self.integrateAll()

    def countAndFetchEvents(self, search_str = '\t0\n', alt_search_str = '\t0\r\n', lines_to_skip = 2):
        lines = 0
        events = []
        event_flag = False

        for line in self.csvfile:
            if line.endswith(search_str) or line.endswith(alt_search_str):
                event_flag = False
            elif event_flag == False and lines > lines_to_skip - 1:
                event_flag = True
                events.append(lines - lines_to_skip)
            lines += 1

        return lines - lines_to_skip, events

    def load(self):

        print >>sys.stderr, "loading file", self.datafile

        try:
            # rewind file
            self.csvfile.seek(0, 0)

            #skip the first two lines (heather and units)
            self.csvfile.readline().rstrip('\n')
            self.csvfile.readline().rstrip('\n')

            nrow = 0

            for datarow in self.csvfile:
                try:
                    daytime, self.datastring = datarow.split('\t', 1)
                    self.fileDaytime[nrow]=daytime
                    self.datavector = [ast.literal_eval(s)
                                        for s in self.datastring.split( )]
                    i = 0
                    for k in self.keys:
                        if i==0:
                            self.fileData[i][nrow] = self.datavector[self.keymap[i]]/4
                        else:
                            self.fileData[i][nrow] = self.datavector[self.keymap[i]]
                        i += 1
                except:
                    print >>sys.stderr, "Skipping bad row at line", nrow

                nrow += 1

        except Exception as e:
            print >>sys.stderr, e
            raise
        else:
           print >>sys.stderr, "loaded successfully"
           self.csvfile.close()

    def loadLast(self):

        print >>sys.stderr, "loading last event of ", self.datafile

        try:

            # rewind file
            self.csvfile.seek(0, 0)
            #skip the first two lines (heather and units) to find datastart point
            self.csvfile.readline().rstrip('\n')
            self.csvfile.readline().rstrip('\n')
            nrow = 0
            firstrow = 0

###            #  more than one event, then load data starting from previous one
###            if self.numEvents > 1:
###                firstrow = self.results.index[self.numEvents-2]

            # load 10 lines to establish average sampling rate
            for datarow in self.csvfile:
                #print >>sys.stderr, datarow
                daytime, self.datastring = datarow.split('\t', 1)
                self.fileDaytime[nrow]=daytime
                self.datavector = [ast.literal_eval(s)
                                   for s in self.datastring.split( )]
                i = 0
                for k in self.keys:
                    if i==0:
                        self.fileData[i][nrow] = self.datavector[self.keymap[i]]/4
                    else:
                        self.fileData[i][nrow] = self.datavector[self.keymap[i]]
                    i += 1
                nrow += 1
                if nrow > 9:
                    break
            # calculate the number of datapoints per second
            timestep   = self.fileData.runtime[nrow-1]-self.fileData.runtime[0]
            timestep  /= nrow - 1

            print >>sys.stderr, "Average sampling rate", timestep
            firstrow = int(self.results.index[self.numEvents-1] - self.baselinelength*timestep*2)
            if firstrow < 0: firstrow = 0

            print >>sys.stderr, "Index of last event:", self.results.index[self.numEvents-1]
            print >>sys.stderr, "Loading file from position row index", firstrow

            for datarow in self.csvfile:
                if nrow >= firstrow:
                    daytime, self.datastring = datarow.split('\t', 1)
                    self.fileDaytime[nrow]=daytime
                    self.datavector = [ast.literal_eval(s)
                                       for s in self.datastring.split( )]
                    i = 0
                    for k in self.keys:
                        self.fileData[i][nrow] = self.datavector[self.keymap[i]]
                        i += 1
                nrow += 1

        except Exception as e:
            print >>sys.stderr, e
            raise
        else:
           print >>sys.stderr, "loaded successfully"
           self.csvfile.close()

    def findEvents_old(self):

        print >>sys.stderr, "Searching for events"

        eventIndex    = []
        eventRuntime  = []
        self.eventDaytime = []


        i = 0
        cdstatus = 0
        for count in self.fileData.countdown:
            if count > 0 and cdstatus == 0:
                eventIndex   = np.append(eventIndex, int(i))
                eventRuntime = np.append(eventRuntime, self.fileData.runtime[i])
                self.eventDaytime.append(self.fileDaytime[i])
            cdstatus = count
            i += 1

        self.numEvents = len(eventIndex)
        self.results   = self.eventResult._make(np.zeros(
                         (np.shape(self.eventKeys)[0],self.numEvents)))
        self.results   = self.results._replace(**{"index":eventIndex})
        self.results   = self.results._replace(**{"runtime":eventRuntime})
        print >>sys.stderr, self.numEvents, "events found"

    def loadEventsData(self):

        eventRuntime  = []
        self.eventDaytime = []

        for event_index in self.results.index:
            eventRuntime = np.append(eventRuntime, self.fileData.runtime[event_index])
            self.eventDaytime.append(self.fileDaytime[event_index])

        self.results   = self.results._replace(**{"runtime":eventRuntime})

    def calculateEventBaseline(self, eventIndex):
        if eventIndex < 0:
           eventIndex = self.numEvents - 1

        if eventIndex >= self.numEvents:
           try:
               raise EventError(2)
           except EventError as e:
               print >>sys.stderr, "Event out of range"
        else:
#            print >>sys.stderr, "Finding baseline", eventIndex + 1
            i0 = int(self.results.index[eventIndex])
            i1 = i0
            elapsedTime = self.results.runtime[eventIndex] - self.fileData.runtime[i0]
            while elapsedTime <= self.baselinelength and i1 >= 0:
                i1 -= 1
                elapsedTime = self.results.runtime[eventIndex] - self.fileData.runtime[i1]
            else:
                i1 += 1
            self.results.baseline[eventIndex] = np.mean(self.fileData.co2[i1:i0])

    def calculateAllBaseline(self):

         for event in range(0,self.numEvents):
            self.calculateEventBaseline(event)

    def integrateEvent(self, eventIndex = -1):

       if eventIndex < 0:
           eventIndex = self.numEvents - 1
           print >>sys.stderr, "Integrating last event: event number", eventIndex + 1
       elif eventIndex >= self.numEvents:
           try:
               raise EventError(1)
           except EventError as e:
               print >>sys.stderr, "Event", eventIndex , "out of range"
           #print >>sys.stderr, "Event out of range"
           #raise
           return
#       else:
#           print >>sys.stderr, "Integrating event number", eventIndex + 1

       i0 = int(self.results.index[eventIndex])
       i1 = i0
       elapsedTime = self.fileData.runtime[i0] - self.results.runtime[eventIndex]
       while elapsedTime <= self.integrationlength and i1 < self.numSamples - 1:
           i1 += 1
           elapsedTime = self.fileData.runtime[i1] - self.results.runtime[eventIndex]
       else:
           if elapsedTime <= self.integrationlength and i1 == self.numSamples - 1:
               print >>sys.stderr, 'End of file reachead while integrating last event ({0})!'.format(self.eventDaytime[eventIndex])
           i1 -= 1

       co2     = (self.fileData.co2[i0:i1]-self.results.baseline[eventIndex])*ppmtoug
       runtime = self.fileData.runtime[i0:i1]/60
       flow    = self.fileData.flow[i0:i1]
       deltatc  = co2*flow

#       tc_s = simps(deltatc, runtime)
       tc_t = np.trapz(deltatc, x=runtime)

       self.results.tc[eventIndex] = tc_t
       self.results.maxtoven[eventIndex] = max(self.fileData.toven[i0:i1])

       return tc_t

    def integrateAll(self):

        #print "hello, integrating", self.numEvents, "events"
        for event in range(0,self.numEvents):
            self.integrateEvent(event)

    def printResults(self, header = True, all = True):

        formatString = '{0}\t{1:.0f}\t{2:.2f}\t{3:.2f}\t{4:.0f}\t{5:.2f}'

        if header:
            print "datafile:", self.datafile
            print 'event time\tindex\truntime\tco2 base\tmax T_oven\ttc'
            print 'hh:mm:ss\t-\tseconds\tppm\tdegC\tug'

        if all:
            for event in range(0,self.numEvents):
                print formatString.format(self.eventDaytime[event],
                            self.results.index[event],
                            self.results.runtime[event], self.results.baseline[event],
                            self.results.maxtoven[event], self.results.tc[event])
        else:
            event = self.numEvents - 1
            print formatString.format(self.eventDaytime[event],
                            self.results.index[event],
                            self.results.runtime[event], self.results.baseline[event],
                            self.results.maxtoven[event], self.results.tc[event])

    def uploadData(self, date, all = True):

        #date = time.strftime("%Y-%m-%d")
        myUploader = Uploader()

        if all:
            for event in range(0,self.numEvents):
                data   = {}
                values = [
                    date,
                    self.eventDaytime[event],
                    self.datafile,
                    self.results.index[event],
                    self.results.runtime[event],
                    self.results.baseline[event],
                    self.results.maxtoven[event],
                    self.results.tc[event]]
                i = 0
                for k in self.uploadKeys:
                    data[k] = values[i]
                    i += 1
                myUploader.httpsend(data)
        else:
            event = self.numEvents - 1
            data   = {}
            values = [
                    date,
                    self.eventDaytime[event],
                    self.datafile,
                    self.results.index[event],
                    self.results.runtime[event],
                    self.results.baseline[event],
                    self.results.maxtoven[event],
                    self.results.tc[event]]
            i = 0
            for k in self.uploadKeys:
                data[k] = values[i]
                i += 1
            myUploader.httpsend(data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process FatCat datafiles.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                    nargs='?', default="extras/SampleData.txt",
                    help='file to be processed. Leave empty to test with extras/SampleData.txt')
    head_parser = parser.add_mutually_exclusive_group(required=False)
    head_parser.add_argument('--header', dest='head', action='store_true',
                    help='include file header in output (default)')
    head_parser.add_argument('--no-header', dest='head', action='store_false',
                    help='print only calculated event data')
    parser.set_defaults(head=True)
    all_parser = parser.add_mutually_exclusive_group(required=False)
    all_parser.add_argument('--all', dest='all', action='store_true',
                    help='calculate tc for all events (default)')
    all_parser.add_argument('--last', dest='all', action='store_false',
                    help='include only last event')
    parser.set_defaults(all=True)
    upload_parser = parser.add_mutually_exclusive_group(required=False)
    upload_parser.add_argument('--upload', dest='upload', action='store_true',
                    help='upload data to cloud')
    upload_parser.add_argument('--no-upload', dest='upload', action='store_false',
                    help='do not upload data (default)')
    parser.set_defaults(upload=False)
    parser.add_argument('--usedate', required=False, dest='DATE',
                    help='Use this date for the generated result table (DATE=Today if omitted). Format: YYYY-MM-DD')

    args = parser.parse_args()

    if args.DATE:
        date = args.DATE
    else:
        date = time.strftime("%Y-%m-%d")

    with args.datafile as file:
        mydata = Datafile(file)

        try:
            if args.all:
                mydata.load()
                mydata.loadEventsData()
                mydata.calculateAllBaseline()
                mydata.integrateAll()
            else:
                mydata.loadLast()
                mydata.loadEventsData()
                mydata.calculateEventBaseline(-1)
                mydata.integrateEvent(-1)
            mydata.printResults(header = args.head, all = args.all)
        except:
            print >>sys.stderr, "Oops!  could not calculate tc table.  Try again..."

        #try:
        if args.upload:
                mydata.uploadData(date, all = args.all)
        #except:
            #print >>sys.stderr, "Oops!  could not upload data to cloud."
