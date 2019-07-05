#!/usr/bin/env python

import configparser, argparse        # for argument parsing
import os, sys
import ast             # for datastring parsing
from collections import namedtuple
import numpy as np
import time, datetime  # required by the uploadData function

sys.path.append('./extras/')

from fatcat_uploader import Uploader # httpsend command for uploading data
from fatcat_uploader import FileUploader # httpsend command for uploading data
#import math
#from scipy.integrate import simps   ### if simpson's rule integration (instead of trapezoidal) is required.
import re              # for regular expression matching

ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm

def validdate(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

class EventError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Datafile(object):
    def __init__(self, datafile, events_path = 'data/events/', integral_length = 65, data_length = 120): # datafile is a valid filepointer

        #init data structure
        self.datastring = ""
        self.eventfileSuffix = "-eventdata.csv"
        self.datafile   = datafile.name
        self.csvfile    = datafile
        self.eventDir = events_path
        self.date       = time.strftime("%Y-%m-%d")
        self.lines2skip = 5                         # skip file headers plus first two lines due to uknown errors
        self.skipedlines = []

        print >>sys.stderr, '{1}\nCounting events in datafile "{0}"'.format(self.datafile, time.asctime( time.localtime(time.time()) ))
        self.numSamples, events = self.countAndFetchEvents(lines_to_skip = self.lines2skip)
        if events[-1] >= self.numSamples:
           events = events[:len(events)-1]
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
        print >>sys.stderr, '{0} lines of data.\n{1} event(s) found at index(es): {2}'.format(self.numSamples, len(self.results.index), self.results.index)

        self.baselinelength    = 5               # time for baseline calculation in seconds
        self.datalength        = data_length     # seconds of data for event file
        self.integrallength = integral_length # length of integration in seconds
        #self.uploadDelay       =   5 # seconds to wait between each db insert command

        self.filekeys = [
        #    "daytime",             ### first column of the datafile is skipped because it is not an integer
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
            "countdown"]            ### the additional column, i.e. status_byte, is hex and thus also not readed with the integer parser

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

        self.fileunits = [
        #    "hh:mm:ss",
            "s",
            "degC",
            "degC",
            "degC",
            "degC",
            "degC",
            "degC",
            "degC",
            "degC",
            "degC",
            "kPa",
            "ppm",
            "lpm",
            "A",
            "s"]

        self.uploadKeys = [
            "date",
            "time",
            "datafile",
            "dataindex",
            "runtime",
            "co2base",
            "tempoven",
            "tc",
            "userfile"]

        # generates a key map from (all) the datafile to the reduced list used here
        self.keymap = []
        self.units   = []
        for k in self.keys:
            i = self.filekeys.index(k)
            self.keymap.append(i)
            self.units.append(self.fileunits[i])

        self.tcaData = namedtuple("tcaData", self.keys)
        self.fileData = self.tcaData._make(np.zeros((np.shape(self.keys)[0],
                        self.numSamples)))

    def countAndFetchEvents(self, search_str = '.*\t0\t..\n', alt_search_str = '.*\t0\t..\r\n', lines_to_skip = 3):
        lines = 0
        events = []
        event_flag = False

        regex1 = re.compile(search_str)
        regex2 = re.compile(alt_search_str)

        for line in self.csvfile:
            if lines < lines_to_skip:
                self.skipedlines.append(line)
            elif re.match(regex1, line) or re.match(regex2, line):
                event_flag = False
            elif event_flag == False: # and lines > lines_to_skip - 1:
                event_flag = True
                events.append(lines - lines_to_skip)
            lines += 1

        return lines - lines_to_skip, events

    def load(self):

        print >>sys.stderr, "loading file", self.datafile

        try:
            # rewind file
            self.csvfile.seek(0, 0)

            #skip the first three lines (date, heather and units)
            try:
                date = self.csvfile.readline().rstrip('\n')
                validdate(date)
                self.date = date
            except:
                print >>sys.stderr, "no date at the beginning of the file"
            for i in range(1, self.lines2skip):
                self.csvfile.readline().rstrip('\n')

            nrow = 0

            for datarow in self.csvfile:
                try:
                    daytime, self.datastring = datarow.split('\t', 1)
                    self.fileDaytime[nrow]=daytime

                    self.datavector = []
                    i = 0
                    for s in self.datastring.split( ):
                       if i < len(self.filekeys):
                         #### use this values als integers
                         self.datavector.append(ast.literal_eval(s))
                       i += 1

                    i = 0
                    for k in self.keys:
                        self.fileData[i][nrow] = self.datavector[self.keymap[i]]
                        i += 1
                except:
                    print >>sys.stderr, "Skipping bad row at line", nrow, ":", datarow

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
            #skip the first three lines (date, heather and units)
            try:
                date = self.csvfile.readline().rstrip('\n')
                validdate(date)
                self.date = date
            except:
                print >>sys.stderr, "no date at the beginning of the file"
            for i in range(1, self.lines2skip):
                self.csvfile.readline().rstrip('\n')

            nrow = 0
            firstrow = 0

            # load 10 lines to establish average sampling rate
            for datarow in self.csvfile:
                #print >>sys.stderr, datarow
                daytime, self.datastring = datarow.split('\t', 1)
                self.fileDaytime[nrow]=daytime
                ####### Changed for the status byte...
                ####### ignores additional variables at the end
                self.datavector = []
                i = 0
                for s in self.datastring.split( ):
                    if i < len(self.filekeys):
                         #### use this values als integers
                         self.datavector.append(ast.literal_eval(s))
                    i += 1

                i = 0
                for k in self.keys:
                    self.fileData[i][nrow] = self.datavector[self.keymap[i]]
                    i += 1
                nrow += 1
                if nrow > 9:
                    break
            # calculate the number of datapoints per second
            timestep   = self.fileData.runtime[nrow-1]-self.fileData.runtime[0]
            timestep  /= nrow - 1

            print >>sys.stderr, "Average timestep in seconds:", timestep
            firstrow = int(self.results.index[self.numEvents-1] - self.baselinelength*2/timestep)
            if firstrow < 0: firstrow = 0

            print >>sys.stderr, "Index of last event:", self.results.index[self.numEvents-1]
            print >>sys.stderr, "Loading file from position row index", firstrow

            for datarow in self.csvfile:
                if nrow >= firstrow:
                    daytime, self.datastring = datarow.split('\t', 1)
                    self.fileDaytime[nrow]=daytime
                    self.datavector = []
                    i = 0
                    for s in self.datastring.split( ):
                        if i < len(self.filekeys):
                            #### use this values als integers
                            self.datavector.append(ast.literal_eval(s))
                        i += 1
                    
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
            self.results.baseline[eventIndex] = np.mean(self.fileData.co2[i1:i0]).round(3)

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
           return

       i0 = int(self.results.index[eventIndex])
       i1 = i0
       elapsedTime = self.fileData.runtime[i0] - self.results.runtime[eventIndex]
       j = 0
       while elapsedTime <= self.datalength and i1 < self.numSamples - 1:
           i1 += 1
           elapsedTime = self.fileData.runtime[i1] - self.results.runtime[eventIndex]
           # search for index 
           if elapsedTime <= self.integrallength:
               j += 1
       else:
           if elapsedTime <= self.datalength and i1 == self.numSamples - 1:
               print >>sys.stderr, 'End of file reachead while integrating last event ({0})!'.format(self.eventDaytime[eventIndex])
           i1 -= 1

       co2     = (self.fileData.co2[i0:i1]-self.results.baseline[eventIndex])
       runtime = self.fileData.runtime[i0:i1]
       flow    = self.fileData.flow[i0:i1]
       #deltatc  = co2*np.mean(flow)*ppmtoug        ### Evaluate TC using the average flow
       deltatc  = co2*flow*ppmtoug                 ### Evaluate TC using real time flow
       integral_y = deltatc[:j]
       integral_x = runtime[:j]
       #tc_s = simps(deltatc, runtime)/60           ### Integrate using simpson's rule
       #tc_t = np.trapz(deltatc, x=runtime)/60      ### Integrate using trapezoidal rule
       tc_t = np.trapz(integral_y, x=integral_x)/60 ### Integrate using trapezoidal rule

       co2 = co2.round(3)
       deltatc = deltatc.round(3)
       self.results.tc[eventIndex] = tc_t.round(3)
       self.results.maxtoven[eventIndex] = max(self.fileData.toven[i0:i1])

       self.saveEvent(i0, i1, deltatc, co2)

       return i0, i1

    def saveEvent(self, i0, i1, deltatc, co2):  #### create output file for event

       filename = ""
       filename = self.date + "-" + self.fileDaytime[i0][0:2] + self.fileDaytime[i0][3:5] + "-eventdata.csv"

       newfile = self.eventDir + filename
       fo = open(newfile, "w")
       fo.write(filename)
       fo.write('\n')
       fo.write("source: ")
       fo.write(self.datafile)
       fo.write('\n')
       outputString = "time"
       for k in self.keys:
           outputString += ", " + k
       outputString += ", co2-event, dtc\n"
       fo.write(outputString)

       outputString = "hh:mm:ss"
       for k in self.units:
           outputString += ", " + k
       outputString += ", ppm, ug/min\n"
       fo.write(outputString)

       for row in range(i0, i1):
           outputString = ""
           outputString += self.fileDaytime[row]
           col = 0
           for k in self.keys:
               outputString += "," + str(self.fileData[col][row])
               col += 1
           outputString += "," + str(co2[row - i0]) + "," + str(deltatc[row - i0]) + "\n"
           fo.write(outputString)
         
       fo.close()

    def integrateAll(self):

        #print "hello, integrating", self.numEvents, "events"
        for event in range(0,self.numEvents):
            i0, i1 = self.integrateEvent(event)

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

    def uploadData(self, date, all = True, istart = 0):

        if len(date) == 0:
            date = self.date
        myUploader = FileUploader()

        if all:
            j = 1
            for event in range(0,self.numEvents):
                filename = self.eventDir + self.date + "-" + self.eventDaytime[event][0:2] + self.eventDaytime[event][3:5] + self.eventfileSuffix
                data   = {}
                values = [
                    date,
                    self.eventDaytime[event],
                    self.datafile,
                    self.results.index[event],
                    self.results.runtime[event],
                    self.results.baseline[event],
                    self.results.maxtoven[event],
                    self.results.tc[event],
                    open(filename, 'r')]
                i = 0
                for k in self.uploadKeys:
                    data[k] = values[i]
                    i += 1
                if j > istart:
                    print >>sys.stderr, "Datapoint", j, ", event file:", filename
                    myUploader.httpsend(data)
                else:
                    print >>sys.stderr, "Skipping upload of datapoint", j
                j += 1
        else:
            event = self.numEvents - 1

            filename = self.eventDir + self.date + "-" + self.eventDaytime[event][0:2] + self.eventDaytime[event][3:5] + self.eventfileSuffix
            data   = {}
            
            values = [
                    date,
                    self.eventDaytime[event],
                    self.datafile,
                    self.results.index[event],
                    self.results.runtime[event],
                    self.results.baseline[event],
                    self.results.maxtoven[event],
                    self.results.tc[event],
                    open(filename, 'r')]
            i = 0
            for k in self.uploadKeys:
                data[k] = values[i]
                i += 1
            
            print >>sys.stderr, "Event file:", filename
            myUploader.httpsend(data)

if __name__ == "__main__":

    #config_file = args.INI
    config_file = 'config.ini'
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        data_length = eval(config['DATA_ANALYSIS']['EVENT_LENGTH'])
        integral_length = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
    else:
        events_path = './data/events/'  # if ini file cannot be found
        data_length = 120
        integral_length = 65
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

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
    parser.add_argument('--startindex', required=False, dest='istart', type=int,
                    help='Use this if you want to start uploading data at an index other than the first (i.e. i>0). This option is for errors in the uploading process')
#    parser.add_argument('--inifile', required=False, dest='INI', default='config.ini',
#                    help='Path to configuration file (config.ini if omitted)')
    parser.add_argument('--intlength', dest='intlength', type=int, default=integral_length,
                    help='Set the length of the integration time in seconds. Must be shorter than data length (default {}s)'.format(integral_length))
    parser.add_argument('--datalength', dest='datalength', type=int, default=data_length,
                    help='Set the length of the integration time in seconds (default {}s)'.format(data_length))

    args = parser.parse_args()

    if args.DATE:
        date = args.DATE
        validdate(date)
    else:
        date = ""

    if args.istart:
        startIndex = args.istart
    else:
        startIndex = 0
        
#    if args.intlength:
#        integral_length = args.intlength
#    else:
#        integral_length = 630
    integral_length = args.intlength
    data_length = args.datalength


    with args.datafile as file:
        mydata = Datafile(file, events_path=events_path, integral_length = integral_length, data_length = data_length)

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
                i0, i1 = mydata.integrateEvent(-1)
            mydata.printResults(header = args.head, all = args.all)
        except:
            print >>sys.stderr, "Oops!  could not calculate tc table.  Try again..."
            raise

        if args.upload:
                print >>sys.stderr, "uploading events to DB..."
                mydata.uploadData(date, all = args.all, istart = startIndex)
