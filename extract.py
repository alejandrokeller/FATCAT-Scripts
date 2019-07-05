#!/usr/bin/env python

import configparser, argparse        # for argument parsing
import os, sys
import ast             # for datastring parsing
from collections import namedtuple
import numpy as np
import time, datetime  # required by the uploadData function
import pandas as pd

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

class Rawfile(object):
    def __init__(self, datafile, events_path, integral_length, data_length): # datafile is a valid filepointer

        #init data structure
        self.datastring = ""
        self.eventfileSuffix = "-eventdata.csv"
        self.datafile   = datafile.name
        self.csvfile    = datafile
        self.eventDir = events_path
        self.date       = time.strftime("%Y-%m-%d")
        self.skipedlines = []

        self.eventKeys = [
            "index",
            "runtime",
            "daytime",
            "baseline",
            "maxtoven",
            "tc"]

        self.resultsDf = pd.DataFrame(columns = self.eventKeys)
        
        self.baselinelength    = 5               # time for baseline calculation in seconds
        self.datalength        = data_length     # seconds of data for event file
        self.integrallength = integral_length    # length of integration in seconds

        self.keys = [
            "Daytime",
            "Time",
        #    "Sp Oven",
            "T Oven",
        #    "Max Allowed Coil",
        #    "T Coil",
        #    "Sp Band",
        #    "T Band",
        #    "Ext Flow",
        #    "T Cat",
        #    "CO2 Cell T",
            "CO2 Cell P",
            "CO2",
            "Flowrate",
        #    "Ind. Current",
            "Cycle Countdown"]

        #### For compatibility with prior version #####
        self.keyDict = {
            "Daytime":"time",
            "Time":"runtime",
        #    "Sp Oven",
            "T Oven":"toven",
        #    "Max Allowed Coil",
        #    "T Coil",
        #    "Sp Band",
        #    "T Band",
        #    "Ext Flow",
        #    "T Cat",
        #    "CO2 Cell T",
            "CO2 Cell P":"pco2",
            "CO2":"co2",
            "Flowrate":"flow",
        #    "Ind. Current",
            "Cycle Countdown":"countdown"}

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

        self.fileData = pd.DataFrame(columns = self.keys)
        self._load()
        
        print >>sys.stderr, '{1}\nCounting events in datafile "{0}"'.format(self.datafile, time.asctime( time.localtime(time.time()) ))
        events = self._countAndFetchEvents()
        # in case there is not enough data for the last event ignore it
        if events[-1] >= self.numSamples - data_length*2: 
           events = events[:-2]
        self.numEvents  = len(events)

        print >>sys.stderr, '{0} lines of data.\n{1} event(s) found at index(es): {2}'.format(self.numSamples, len(self.resultsDf), events)

    def _countAndFetchEvents(self):
        events = []
        event_flag = False

        for index, row in self.df.iterrows():
            if row['Cycle Countdown'] == 0:
                event_flag = False
            elif (event_flag == False and row['Cycle Countdown'] > 0):
                event_flag = True
                events.append(index)
                self.resultsDf = self.resultsDf.append(
                    {self.eventKeys[0]: int(index), self.eventKeys[1]: row['Time'], self.eventKeys[2]: row['Daytime']},
                    ignore_index=True).fillna(0)

        return events

    def _read_header(self):
        # rewind file
        self.csvfile.seek(0, 0)

        #skip the first three lines (date, heather and units)
        try:
            date = self.csvfile.readline().rstrip('\n')
            validdate(date)
            self.date = date
            self.skiprows = 3
            self.header = 1
        except:
            print >>sys.stderr, "no date at the beginning of the file"
            self.csvfile.seek(0, 0)
            self.skiprows = 2
            self.header = 0
        self.raw_file_keys  = self.csvfile.readline().rstrip('\n').split('\t')
        self.raw_file_units = self.csvfile.readline().rstrip('\n').split('\t')

        # generates a units dictionary
        self.unitsDict = dict(zip(self.raw_file_keys, self.raw_file_units))

    def _load(self):

        print >>sys.stderr, "loading file", self.datafile

        try:
            self._read_header()
            self.csvfile.seek(0, 0)
            columns = pd.read_csv(self.csvfile, header=self.header, nrows = 1, sep='\t', parse_dates=True).columns
            self.csvfile.seek(0, 0)
            self.df = pd.read_csv(self.csvfile, skiprows = self.skiprows, sep='\t', parse_dates=True, header = None, names=columns, usecols = self.keys)

            self.numSamples = len(self.df.index)

        except Exception as e:
            print >>sys.stderr, e
            raise
        else:
           print >>sys.stderr, "loaded successfully"
           self.csvfile.close() 

    def calculateEventBaseline(self, eventIndex):
        if eventIndex < 0:
           eventIndex = self.numEvents - 1

        if eventIndex >= self.numEvents:
           try:
               raise EventError(2)
           except EventError as e:
               print >>sys.stderr, "Event out of range"
        else:
            i0 = int(self.resultsDf['index'][eventIndex])
            runtime = self.resultsDf['runtime'][eventIndex]
            i1 = i0
            elapsedTime = runtime - self.df['Time'][i1]
            while elapsedTime <= self.baselinelength and i1 >= 0:
                i1 -= 1
                elapsedTime = runtime - self.df['Time'][i1]
            else:
                i1 += 1
            return np.mean(self.df['CO2'][i1:i0]).round(3)

    def calculateAllBaseline(self):

        baselines = []
        for event in range(0,self.numEvents):
            baselines.append(self.calculateEventBaseline(event))
        self.resultsDf['baseline'] = baselines

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

       i0 = int(self.resultsDf['index'][eventIndex])
       runtime = self.resultsDf['runtime'][eventIndex]
       i1 = i0
       elapsedTime = self.df['Time'][i1] - runtime
       j = 0
       while elapsedTime <= self.datalength and i1 < self.numSamples - 1:
           i1 += 1
           elapsedTime = self.df['Time'][i1] - runtime
           # search for index 
           if elapsedTime <= self.integrallength:
               j += 1
       else:
           if elapsedTime <= self.datalength and i1 == self.numSamples - 1:
               print >>sys.stderr, 'End of file reachead while integrating last event ({0})!'.format(self.resultsDf['daytime'][eventIndex])
           i1 -= 1

       co2     = (self.df['CO2'][i0:i1]-self.resultsDf['baseline'][eventIndex])
       seconds = self.df['Time'][i0:i1]
       flow    = self.df['Flowrate'][i0:i1]
       #deltatc  = co2*np.mean(flow)*ppmtoug        ### Evaluate TC using the average flow
       deltatc  = co2*flow*ppmtoug                 ### Evaluate TC using real time flow
       integral_y = deltatc[:j]
       integral_x = seconds[:j]
       #tc_s = simps(deltatc, runtime)/60           ### Integrate using simpson's rule
       #tc_t = np.trapz(deltatc, x=runtime)/60      ### Integrate using trapezoidal rule
       tc_t = np.trapz(integral_y, x=integral_x)/60 ### Integrate using trapezoidal rule

       co2 = co2.round(3)
       deltatc = deltatc.round(3)
       tc = tc_t.round(3)
       maxT = max(self.df['T Oven'][i0:i1])
       dtcDf = pd.concat([co2,deltatc], axis = 1)
       newColNames = ['co2-event', 'dtc']
       dtcDf.columns = ['co2-event', 'dtc']

       self.saveEvent(i0, i1, dtcDf, newColNames = newColNames, newUnits = ['ppm', 'ug/min'])

       return tc, maxT

    def saveEvent(self, i0, i1, df, newColNames, newUnits):  #### create output file for event

        units = []
        colNames = []
        for k in self.keys:
            key = str(k)
            #units.append(self.unitsDict[key.replace(" ","")])
            units.append(self.unitsDict[key])
            colNames.append(self.keyDict[key])
        colNames = colNames + newColNames
        units = units + newUnits

        valuesDf = pd.concat([self.df.iloc[i0:i1],df], axis = 1)

        filename = self.date + "-" + self.df['Daytime'][i0][0:2] + self.df['Daytime'][i0][3:5] + "-eventdata.csv"
        newfile = self.eventDir + filename
        
        header = filename + "\nsource: " + self.datafile + "\n" + ",".join(colNames) + "\n" + ",".join(units) + "\n"
        with open(newfile, "w") as fw:
            fw.write(header)
            valuesDf.to_csv(fw, index=False, header=False)
            fw.close()

    def integrateAll(self):

        tc_data = []
        temp_data = []
        for event in range(0,self.numEvents):
            tc, temp = self.integrateEvent(event)
            tc_data.append(tc)
            temp_data.append(temp)
        self.resultsDf['maxtoven'] = temp_data
        self.resultsDf['tc'] = tc_data

    def printResults(self, header = True, all = True):

        formatString = '{0}\t{1:.0f}\t{2:.2f}\t{3:.2f}\t{4:.0f}\t{5:.2f}'

        if header:
            print "datafile:", self.datafile
            print 'event time\tindex\truntime\tco2 base\tmax T_oven\ttc'
            print 'hh:mm:ss\t-\tseconds\tppm\tdegC\tug'

        if all:
            start = 0
        else:
            start = self.numEvents - 1
        for event in range(start,self.numEvents):
                print formatString.format(self.resultsDf['daytime'][event],
                            self.resultsDf['index'][event],
                            self.resultsDf['runtime'][event], self.resultsDf['baseline'][event],
                            self.resultsDf['maxtoven'][event], self.resultsDf['tc'][event])

    def uploadData(self, date, all = True, istart = 0):

        if len(date) == 0:
            date = self.date
        myUploader = FileUploader()

        if all:
            start = 0
        else:
            start = self.numEvents - 1
        j = 1
        for event in range(start,self.numEvents):
            filename = self.eventDir + self.date + "-" + self.resultsDf['daytime'][0:2] + self.resultsDf['daytime'][3:5] + self.eventfileSuffix
            data   = {}
            values = [
                date,
                self.resultsDf['daytime'][event],
                self.datafile,
                self.resultsDf['index'][event],
                self.resultsDf['runtime'][event],
                self.resultsDf['baseline'][event],
                self.resultsDf['maxtoven'][event],
                self.resultsDf['tc'][event],
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
        
    integral_length = args.intlength
    data_length = args.datalength

    with args.datafile as file:
        mydata = Rawfile(file, events_path=events_path, integral_length = integral_length, data_length = data_length)

        try:
##                if args.all:
##                    mydata.calculateAllBaseline()
##                    mydata.integrateAll()
##                else:
##                mydata.loadLast()
##                mydata.loadEventsData()
##                mydata.calculateEventBaseline(-1)
##                i0, i1 = mydata.integrateEvent(-1)
            mydata.calculateAllBaseline()
            mydata.integrateAll()
            mydata.printResults(header = args.head, all = args.all)
        except:
            print >>sys.stderr, "Oops!  could not calculate tc table.  Try again..."
            raise

        if args.upload:
                print >>sys.stderr, "uploading events to DB..."
                mydata.uploadData(date, all = args.all, istart = startIndex)
