#!/usr/bin/env python

import configparser, argparse        # for argument parsing
import os, sys, glob
import ast             # for datastring parsing
from collections import namedtuple
import numpy as np
import time, datetime  # required by the uploadData function
import pandas as pd
#import math
#from scipy.integrate import simps   ### if simpson's rule integration (instead of trapezoidal) is required.
import re              # for regular expression matching

base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(base_path + '/extras/')

from fatcat_uploader import Uploader # httpsend command for uploading data
from fatcat_uploader import FileUploader # httpsend command for uploading data
from plot_event import Datafile
from gui import hex2bin

ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm

def validdate(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

def iserror(func, *args, **kw):
    try:
        func(*args, **kw)
        return False
    except Exception:
        return True

# converter to catch errors in csv files 
def conv(val):
    if not val:
        return np.nan
    try:
        return np.float64(val)
    except:        
        return np.nan

class EventError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Rawfile(object):
    def __init__(self, datafile, events_path, integral_length,
                 data_length, baseline_length, all_events = True,
                 baseline = False): # datafile is a valid filepointer

        #init data structure
        self.datastring = ""
        self.eventfileSuffix = "-eventdata.csv"
        self.datafile   = datafile.name
        self.csvfile    = datafile
        self.eventDir = events_path
        self.date       = time.strftime("%Y-%m-%d")
        self.skipedlines = []
        self.baseline = baseline

        self.eventKeys = [
            "index",
            "runtime",
            "daytime",
            "baseline",
            "maxtoven",
            "tc"]

        self.resultsDf = pd.DataFrame(columns = self.eventKeys)
        
        self.baselinelength    = baseline_length # time for baseline calculation in seconds
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
            "Ext flow",
        #    "T Cat",
        #    "CO2 Cell T",
            "CO2 Cell P",
            "CO2",
            "Flowrate",
        #    "Ind. Current",
            "Cycle Countdown",
            "Status Byte"]

        # columns to save on the event file
        self.eventfileKeys = self.keys[:]
        self.eventfileKeys.remove("Status Byte")
        self.eventfileKeys.remove("Ext flow")

        # force use following data types when reading the rawfile
        self.dtypeDict = {
            #"Daytime":"time",
            "Time":             'float64',
            "Sp Oven":          'float64',
            "T Oven":           'float64',
            "Max Allowed Coil": 'float64',
            "T Coil":           'float64',
            "Sp Band":          'float64',
            "T Band":           'float64',
            "Ext flow":         'float64',
            "T Cat":            'float64',
            "CO2 Cell T":       'float64',
            "CO2 Cell P":       'float64',
            "CO2":              'float64',
            "Flowrate":         'float64',
            "Ind. Current":     'float64',
            "Cycle Countdown":  'float64'}

        #### For compatibility with prior version #####
        self.keyDict = {
            "Daytime":"time",
            "Time":"runtime",
            "Sp Oven":"spoven",
            "T Oven":"toven",
            "Max Allowed Coil":"spcoil",
            "T Coil":"tcoil",
            "Sp Band":"spband",
            "T Band":"tband",
            "Ext flow":"eflow",
            "T Cat":"tcat",
            "CO2 Cell T":"tco2",
            "CO2 Cell P":"pco2",
            "CO2":"co2",
            "Flowrate":"flow",
            "Ind. Current":"curr",
            "Cycle Countdown":"countdown",
            "Status Byte":"statusbyte"}

        # Keys to upload data to a sql database (not been used in long time)
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

        # interpretation of bits on the "Status Byte" column
        self.statusKeys = [
            "valve",   # internal valve
            "pump",    # internal pump
            "fan",
            "oven",    # induction furnace
            "band",    # cat. heater
            "licor",   # external valve
            "res2",    # external pump
            "res"]     

        self.fileData = pd.DataFrame(columns = self.keys)
        self._load()
        
        print >>sys.stderr, '{1}\nCounting events in datafile "{0}"'.format(self.datafile, time.asctime( time.localtime(time.time()) ))
        events = self._countAndFetchEvents()
        # in case there is not enough data for the last event ignore it
        if events[-1] >= self.numSamples - data_length*2: 
           events = events[:-2]
        self.numEvents  = len(events)
            
        self.sample_volume = []
        self.sample_co2 = []
        for event in range(0,self.numEvents):
            volume, co2 = self._calculateSamplingVolume(event)
            self.sample_volume.append(volume)
            self.sample_co2.append(co2)
        self.resultsDf['sample'] = self.sample_volume
        self.resultsDf['sample co2'] = self.sample_co2

        print >>sys.stderr, '{0} lines of data.\n{1} event(s) found at index(es): {2}'.format(self.numSamples, len(self.resultsDf), events)
        if not all_events:
            self.resultsDf = self.resultsDf.iloc[[-1]].reset_index(drop=True)
            self.numEvents = 1
            

    def _countAndFetchEvents(self):
        events = []
        event_flag = False

        # self.on_status is the list of rows of self.df marked with True if "Oven Status" is True
        # value is False otherwise
        for index, row in self.df[self.on_status].iterrows():
            if not events:
                events.append(index)
                event_flag = True
            elif (row['Time'] > self.df['Time'][events[-1]] + self.datalength):
                event_flag = True
                events.append(index)
            if event_flag:
                  event_flag = False
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
            columns = pd.read_csv(self.csvfile, header=self.header, nrows = 1, sep='\t',
                                  parse_dates=True).columns
        except Exception as e:
            print >>sys.stderr, "Could not read the file header"
            print >>sys.stderr, e
            raise
        try:
            self.csvfile.seek(0, 0)
            self.df = pd.read_csv(self.csvfile, skiprows = self.skiprows, sep='\t',
                                  parse_dates=True, header = None, names=columns,
                                  usecols = self.keys, error_bad_lines = False,
                                  dtype = self.dtypeDict
                                  )
            self.numSamples = len(self.df.index)
        except Exception as e:
            print >>sys.stderr, "Error loading file with the standard pandas dtypes, using converter for slow import instead"
            self.csvfile.seek(0, 0)
            newDict = {}
            for key in self.dtypeDict:
                newDict[key]=conv
            self.df = pd.read_csv(self.csvfile, skiprows = self.skiprows, sep='\t',
                                  parse_dates=True, header = None, names=columns,
                                  usecols = self.keys, error_bad_lines = False,
                                  converters = newDict
                                  )
            self.numSamples = len(self.df.index)

        print >>sys.stderr, "loaded successfully"
        # validate status byte to find rows with errors
        mask = self.df['Status Byte'].apply(lambda x: iserror(hex2bin, x))
        #number_of_errors = (mask.values).sum() # fastest way to count errorlines
        errors = self.df['Daytime'][mask].values.tolist()
        # exclude errors
        self.df = self.df[~mask]
        if len(errors):
            print >>sys.stderr, "{} line(s) with 'Status Byte' errors removed at times: {}".format(len(errors), errors)
        # extract oven status
        self.df['Oven Status'] = [bool(int(hex2bin(x)[self.statusKeys.index("oven")])) for x in self.df['Status Byte']]
        self.df['Valve Status'] = [bool(int(hex2bin(x)[self.statusKeys.index("valve")])) for x in self.df['Status Byte']]
        self.df['Pump Status'] = [bool(int(hex2bin(x)[self.statusKeys.index("pump")])) for x in self.df['Status Byte']]
        self.on_status = self.df['Oven Status']==True
        self.sample_on = self.df['Valve Status']==True

        self.csvfile.close()

    def _calculateSamplingVolume(self, eventIndex):
        if eventIndex >= self.numEvents:
           try:
               raise EventError(2)
           except EventError as e:
               print >>sys.stderr, "Event out of range"
        else:
            event_runtime = int(self.resultsDf['runtime'][eventIndex])
            if eventIndex > 0:
                start_runtime = int(self.resultsDf['runtime'][eventIndex - 1])
            else:
                start_runtime = int(self.df['Time'][0])
            df_subset = self.df[(self.df['Valve Status']==False) & (self.df['Time'] >= start_runtime)
                                & (self.df['Time'] < event_runtime)]
            flow = df_subset["Ext flow"] + df_subset["Flowrate"]
            time = df_subset["Time"]
            sample_volume = np.trapz(flow, x=time)/60/1000

            # calculate subset only if the internal pump was active
            df_subset = self.df[(self.df['Pump Status']==True) & (self.df['Valve Status']==False) & (self.df['Time'] >= start_runtime)
                                & (self.df['Time'] < event_runtime)]
            if len(df_subset) > 0:
                co2  = (df_subset["Ext flow"] + df_subset["Flowrate"])*df_subset["CO2"]
                time = df_subset["Time"]
                sample_co2 = np.trapz(co2, x=time)/60/1000/sample_volume # weigthed using sampling flowrate
            else:
                sample_co2 = 0

            return sample_volume, sample_co2
            

    def calculateEventBaseline(self, eventIndex):
        if eventIndex >= self.numEvents:
           try:
               raise EventError(2)
           except EventError as e:
               print >>sys.stderr, "Event out of range"
        else:
            i0 = int(self.resultsDf['index'][eventIndex])
            runtime = self.resultsDf['runtime'][eventIndex]
            i1 = i0
            try:
                elapsedTime = runtime - self.df['Time'].loc[i1]
            except:
                print >>sys.stderr, "error at index=" + str(i1)
                raise
            while (elapsedTime <= self.baselinelength and i1 >= 0):
                i1 = i1 - 1
                elapsedTime = runtime - self.df['Time'].loc[i1]
            else:
                i1 += 1
            # "i0-1" excludes the starting point of the event
            # not necesary, but included for compatibility reasons
            # may be changed to only "i0" without consequences
            return round(np.mean(self.df['CO2'].loc[i1:i0-1]), 2)

    def calculateAllBaseline(self):

        baselines = []
        for event in range(0,self.numEvents):
            baselines.append(self.calculateEventBaseline(event))
        self.resultsDf['baseline'] = baselines

    def integrateEvent(self, eventIndex = -1):

       if eventIndex >= self.numEvents:
           try:
               raise EventError(1)
           except EventError as e:
               print >>sys.stderr, "Event", eventIndex , "out of range"
           return

       i0 = int(self.resultsDf['index'][eventIndex])
       runtime = self.resultsDf['runtime'][eventIndex]
       i1 = i0
       elapsedTime = self.df['Time'].loc[i1] - runtime
       j = 0
       while elapsedTime <= self.datalength and i1 < self.numSamples - 1:
           i1 += 1
           elapsedTime = self.df['Time'].loc[i1] - runtime
           # search for index 
           if elapsedTime <= self.integrallength:
               j += 1
       else:
           if elapsedTime <= self.datalength and i1 == self.numSamples - 1:
               print >>sys.stderr, 'End of file reachead while integrating last event ({0})!'.format(self.resultsDf['daytime'][eventIndex])
           i1 -= 1

       # for back compatibility reasons to have always the same number of lines
       # previous version used iloc instead of loc, thus excluded the last row
       i1 = i1 - 1

       co2     = self.df['CO2'].loc[i0:i1]-self.resultsDf['baseline'][eventIndex]
       seconds = self.df['Time'].loc[i0:i1]
       flow    = (self.df['Flowrate'].loc[i0:i1]).astype('float64')
       
       #deltatc  = co2*np.mean(flow)*ppmtoug        ### Evaluate TC using the average flow
       deltatc  = co2*flow*ppmtoug                 ### Evaluate TC using real time flow
       integral_y = deltatc[:j]
       integral_x = seconds[:j]
       #tc_s = simps(integral_y, integral_x)/60           ### Integrate using simpson's rule
       tc_t = np.trapz(integral_y, x=integral_x)/60 ### Integrate using trapezoidal rule

       co2 = co2.round(3)
       deltatc = deltatc.round(3)
       tc = tc_t.round(3)
       maxT = max(self.df['T Oven'].loc[i0:i1])
       dtcDf = pd.concat([co2,deltatc], axis = 1)
       newColNames = ['co2-event', 'dtc']
       dtcDf.columns = ['co2-event', 'dtc']

       if self.resultsDf['sample'][eventIndex] > 0:
           sample_info = "volume: {:.5f} m^3".format(self.resultsDf['sample'][eventIndex])
           if self.resultsDf['sample co2'][eventIndex] > 0:
               sample_info += "\nsample_co2: {:.1f} ppm (average)".format(self.resultsDf['sample co2'][eventIndex])
       else:
           sample_info = False

       self._saveEvent(i0, i1, dtcDf, newColNames = newColNames, newUnits = ['ppm', 'ug/min'], additional_data = sample_info)

       return tc, maxT

    def _saveEvent(self, i0, i1, df, newColNames, newUnits, additional_data = False):  #### create output file for event

        units = []
        colNames = []
        for k in self.eventfileKeys:
            key = str(k)
            units.append(self.unitsDict[key])
            colNames.append(self.keyDict[key])
        colNames = colNames + newColNames
        units = units + newUnits

        valuesDf = pd.concat([self.df.loc[i0:i1, self.eventfileKeys],df], axis = 1)

        filename = self.date + "-" + self.df['Daytime'].loc[i0][0:2] + self.df['Daytime'].loc[i0][3:5] + "-eventdata.csv"
        newfile = self.eventDir + filename
        
        header = "{}\nsource: {}\n".format(filename, self.datafile)
        if additional_data:
            header = header + additional_data + "\n"
        header = header + ",".join(colNames) + "\n" + ",".join(units) + "\n"
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

    def printResults(self, header = True, all_events = True):
        formatString = '{0}\t{1:.0f}\t{2:.2f}\t{3:.2f}\t{4:.0f}\t{5:.3f}'

        if header:
            col_names = 'event time\tindex\truntime\tco2 base\tmax T_oven\ttc'
            col_units = 'hh:mm:ss\t-\tseconds\tppm\tdegC\tug-C'
            if self.baseline:
                col_names += '\ttc-baseline'
                col_units += '\tug-C'
            if self.sample_volume:
                col_names += '\tsample'
                col_units += '\tm^3'
            if (self.baseline and self.sample_volume):
                col_names += '\ttc conc'
                col_units += '\tug/m^3'
            if self.sample_co2:
                col_names += '\tsample co2'
                col_units += '\tppm'
            print "datafile:", self.datafile
            print col_names
            print col_units

        if all_events:
            start = 0
        else:
            start = self.numEvents - 1
        for event in range(start,self.numEvents):
            data_str = formatString.format(self.resultsDf['daytime'][event],
                            self.resultsDf['index'][event],
                            self.resultsDf['runtime'][event], self.resultsDf['baseline'][event],
                            self.resultsDf['maxtoven'][event], self.resultsDf['tc'][event])
            if self.baseline:
                data_str = data_str + '\t{:.3f}'.format(self.resultsDf['tc'][event] - self.baseline)
            if self.sample_volume:
                data_str = data_str + '\t{:.5f}'.format(self.resultsDf['sample'][event])
            if (self.baseline and self.sample_volume):
                if self.resultsDf['sample'][event] > 0:
                    data_str = data_str + '\t{:.2f}'.format((self.resultsDf['tc'][event] - self.baseline)/self.resultsDf['sample'][event])
                else:
                    data_str = data_str + '\t-'
            if self.sample_co2:
                if self.resultsDf['sample co2'][event] > 0:
                    data_str = data_str + '\t{:.1f}'.format(self.resultsDf['sample co2'][event])
                else:
                    data_str = data_str + '\t-'
            print data_str

    def uploadData(self, date, all_events = True, istart = 0):

        if len(date) == 0:
            date = self.date
        myUploader = FileUploader()

        if all_events:
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
    config_file = base_path + '/config.ini'
    sample_file = base_path + '/extras/SampleData.txt'
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        data_length = eval(config['DATA_ANALYSIS']['EVENT_LENGTH'])
        integral_length = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
        baseline_path = eval(config['DATA_ANALYSIS']['BASELINE_PATH']) + '/'
        baseline_file = eval(config['DATA_ANALYSIS']['BASELINE_FILE'])
        baseline_length = eval(config['DATA_ANALYSIS']['BASELINE_LENGTH'])
        data_path = eval(config['GENERAL_SETTINGS']['DATA_PATH']) + '/'
        data_ext = eval(config['LOGGER']['EXTENSION'])
    else:
        raise ValueError('File \'%s\' is not a valid \'.ini\' file' % config_file)

    parser = argparse.ArgumentParser(description='Process FatCat datafiles.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='List of event files to be processed. Leave empty for newest file')
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
#    parser.add_argument('--inifile', required=False, dest='INI', default=config_file,
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

    # open the baseline DataFrame if it exists
    filename = baseline_path + baseline_file
    if os.path.isfile(filename):
        f = open(filename, 'r')
        baselineFile = Datafile(f, tmax = integral_length)
        baseline = baselineFile.results['tc']
        print >>sys.stderr, "Instrument baseline: {} ug-C".format(baseline)
    else:
        baseline = False

    # Get the last datafile if none is given
    if not args.datafile:
        list_of_datafiles = glob.glob(data_path + '*' + data_ext) # * means all if need specific format then *.csv
        latest_datafile = max(list_of_datafiles, key=os.path.getctime)
##        print >>sys.stderr, "Using file: {}".format(latest_datafile)
        args.datafile = [open(latest_datafile, 'r')]

    for file in args.datafile:
        mydata = Rawfile(file, events_path=events_path,
                         integral_length = integral_length, data_length = data_length,
                         baseline_length = baseline_length, all_events = args.all, baseline = baseline)
        try:
            mydata.calculateAllBaseline()
            mydata.integrateAll()
            mydata.printResults(header = args.head, all_events = args.all)
        except:
            print >>sys.stderr, "Oops!  could not calculate tc table.  Try again..."
            raise

        if args.upload:
                print >>sys.stderr, "uploading events to DB..."
                mydata.uploadData(date, all_events = args.all, istart = startIndex)
