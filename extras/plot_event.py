#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parse
import time, os, glob

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
#print(plt.style.available)

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/', recalculate_co2 = False): # datafile is a valid filepointer
        
        #init data structure
        self.datastring = ""
        self.datafile   = datafile.name
        self.outputDir  = output_path
        self.date       = time.strftime("%Y-%m-%d")
        self.internname = datafile.readline().rstrip('\n') # first line contains the original filename
        self.rawdata    = datafile.readline().rstrip('\n') # second line points to raw data
        self.keys       = datafile.readline().rstrip('\n').replace(" ","").split(',')
        self.units      = datafile.readline().rstrip('\n').replace(" ","").split(',')

        datafile.seek(0, 0)
        self.df = pd.read_csv(datafile, header=[2], skiprows=[3])      # loads the datafile
        datafile.close()
        self.df.columns=self.keys

        if not 'elapsed-time' in self.keys:
            self.keys.append('elapsed-time') # add a new column with the analysis time
            self.units.append('s')
            self.df['elapsed-time'] = self.df['runtime']-self.df['runtime'][0]

        ## recalculate dtc using real time flow instead of the average flow
        #ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm
        #self.df['dtc'] = self.df['co2-event']*self.df['flow']*ppmtoug ### Evaluate TC using real time flow
        if recalculate_co2:
            ## recalculate co2-event using real time flow and dtc
            ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm
            self.df['co2-event'] = self.df['dtc']/(self.df['flow'].mean()*ppmtoug) ### Evaluate TC using real time flow
            self.df['co2-event'] = self.df['co2-event'].round(1)
            self.df['dtc'] = self.df['dtc'].round(3)

        # create event results Dictionary
        self.results = {
            "date": self.extract_date(),
            "time": self.df['time'][0] if 'time' in self.df else '-',
            "runtime": self.df['runtime'][0] if 'runtime' in self.df else '-',
            "co2-base": (self.df['co2'].mean() - self.df['co2-event'].mean()).round(2),
            "maxtemp": max(self.df['toven']),
            "tc": (np.trapz(self.df['dtc'], x=self.df['elapsed-time'])/60).round(3),
            "tc-baseline": (np.trapz(self.df['dtc-baseline'], x=self.df['elapsed-time'])/60).round(3) if 'dtc-baseline' in self.df else '-'
            }
        self.result_units = {
            "date": 'yyyy-mm-dd',
            "time": 'hh:mm:ss',
            "runtime": 's',
            "co2-base": 'ppm',
            "maxtemp": 'degC',
            "tc": 'ug-C',
            "tc-baseline": 'ug-C'
            }

    def extract_date(self):
        date = self.internname[:10]
        if is_date(date):
            return date
        else:
            return '-'

    def add_baseline(self, baseline):
        if 'dtc' in baseline:
            self.keys.append('baseline') # add a new column with the baseline values
            self.units.append('ug/min')
            self.df['baseline'] = baseline['dtc']
            self.keys.append('dtc-baseline') # add a new column with the baseline values
            self.units.append('ug/min')
            self.df['dtc-baseline'] = self.df['dtc']-baseline['dtc']

            # calculate the integral of the newly created column
            self.results["tc-baseline"] = (np.trapz(self.df['dtc-baseline'], x=self.df['elapsed-time'])/60).round(3)

    def create_plot(self, x='elapsed-time', y='dtc', y2='dtc-baseline', style='ggplot', format='pdf', err=False, error_interval = 4):
        plt.style.use('ggplot')
        if err:
            yerr = y + "-sd"
            plt.errorbar(self.df[x], self.df[y], yerr=self.df[yerr], errorevery=error_interval)
        else:
            plt.plot(self.df[x], self.df[y])
            if y2 in self.df:
                plt.plot(self.df[x], self.df[y2])
                plt.legend((y2, y3), loc='upper right')
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y + ' (' + self.units[self.keys.index(y)] + ')'
        plt.title(self.internname)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        filename = self.outputDir + self.internname.replace('.','_') + '_' + y + '.' + format
        plt.savefig(filename)
        plt.show()

    def create_dualplot(self, x='elapsed-time', y1='toven', y2='dtc', y3='dtc-baseline',
                        style='ggplot', format='pdf', y1err=False, y2err=False, error_interval = 4):
        plt.style.use('ggplot')
        
        plt.subplot(2,1,1)
        if y1err:
            yerr = y1 + "-sd"
            plt.errorbar(self.df[x], self.df[y1], yerr=self.df[yerr], errorevery=error_interval)
        else:
            plt.plot(self.df[x], self.df[y1])
        ylabel = y1 + ' (' + self.units[self.keys.index(y1)] + ')'
        plt.title(self.internname)
        plt.ylabel(ylabel)
        
        plt.subplot(2,1,2)
        if y2err:
            yerr = y2 + "-sd"
            plt.errorbar(self.df[x], self.df[y2], yerr=self.df[yerr], errorevery=error_interval)
        else:
            if y2 in self.df:
                plt.plot(self.df[x], self.df[y2])
            if y3 in self.df:
                plt.plot(self.df[x], self.df[y3])
                plt.legend((y2, y3), loc='upper right')
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y2 + ' (' + self.units[self.keys.index(y2)] + ')'
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        filename = self.outputDir + self.internname.replace('.','_') + '_' + y1 + '_' + y2 + '.' + format
        plt.savefig(filename)
        plt.show()

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def create_baseline_file(files, baseline_path, baseline_file):
    # CREATE a DataFrame to Hold the mean value.
    baseline_keys = [
        'elapsed-time',
        'toven',
        'pco2',
        'co2',
        'flow',
        'countdown',
        'co2-event',
        'dtc']

    # CREATE keys for stand. dev. and final csv file
    sd_keys = []
    all_keys = []
    units_list = []
    for k in baseline_keys:
        sd_keys.append(k + '-sd')
        all_keys.append(k)
        all_keys.append(k + '-sd')

    file_list = "" # some text for the file header
    
    df_list = [] # create a list object to hold the DataFrames
    n = 0

    # CREATE a DataFrame to hold the final csv data file
    baseline = pd.DataFrame(columns=all_keys)
    
    for f in files:
        mydata = Datafile(f) # output path is not needed because data will not be plotted

        file_list = file_list + ' ' + mydata.internname
        df_list.append(mydata.df)  # append to the DF list to make the standard dev. calculation 
        
        for k in baseline_keys: # sum up all dataframes
            if n == 0:
                baseline[k] = mydata.df[k]
            else:
                baseline[k] = baseline[k] + mydata.df[k]
        n = n + 1

    for k in baseline_keys:
        baseline[k] = baseline[k]/n # divide through n to calculate mean

        key = sd_keys[baseline_keys.index(k)] # get the relevant sd_key
        baseline[key] = baseline[k]*0 # initialize sd calculation
        for df in df_list:
            baseline[key] = baseline[key] + (df[k] - baseline[k])**2 # sum suare difference to mean

        baseline[key] = (baseline[key]/n)**.5 # calculate std. dev. from the sum of square difference

        # Create list of units to be exported to the CSV-file
        unit = mydata.units[mydata.keys.index(k)]
        units_list.append(unit)
        units_list.append(unit)

    file_list = baseline_file + "\nAverage datafile: " + str(n) + " entries:" + file_list + "\n" + ",".join(all_keys) + "\n" + ",".join(units_list) + "\n"

    filename = baseline_path + baseline_file
    with open(filename, 'w') as f:
        f.write(file_list)
        baseline.to_csv(f, index=False, header=False)
        f.close()

    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Graph generator for fatcat event files.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='List of event files to be processed. Leave empty for newest file')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                        help='Path to configuration file (../config.ini if omitted)')
    zero_parser = parser.add_mutually_exclusive_group(required=False)
    zero_parser.add_argument('--baseline', dest='zero', action='store_true',
                            help='calculate and store baseline from event list')
    zero_parser.add_argument('--plot', dest='zero', action='store_false',
                            help='create plot from event list (default)')
    parser.set_defaults(zero=False)
    t_parser = parser.add_mutually_exclusive_group(required=False)
    t_parser.add_argument('--include-temperature', dest='tplot', action='store_true',
                            help='plot furnace temperature on top (default)')
    t_parser.add_argument('--no-temperature', dest='tplot', action='store_false',
                            help='only plot delta-TC')
    parser.set_defaults(tplot=True)
    fix_parser = parser.add_mutually_exclusive_group(required=False)
    fix_parser.add_argument('--fix-co2', dest='fix', action='store_true',
                            help='fix the co2-event in the event file')
    fix_parser.add_argument('--normal', dest='fix', action='store_false',
                            help='leave event-file as is (default)')
    parser.set_defaults(fix=False)
    
    args = parser.parse_args()
    
    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path   = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        output_path   = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/graph/'
        plot_style    = eval(config['GRAPH_SETTINGS']['PLOT_STYLE'])
        plot_format   = eval(config['GRAPH_SETTINGS']['FILE_FORMAT'])
        error_interval = eval(config['GRAPH_SETTINGS']['ERROR_EVERY'])
        baseline_path = eval(config['DATA_ANALYSIS']['BASELINE_PATH']) + '/'
        baseline_file = eval(config['DATA_ANALYSIS']['BASELINE_FILE'])
    else:
        events_path   = '~/fatcat-files/data/events/'  # if ini file cannot be found
        output_path   = events_path + 'graph/'
        plot_style    = 'ggplot'
        plot_format   = 'pdf'
        baseline_path = '~/fatcat-files/data/baseline/'
        baseline_file = 'zero_event.csv'
        error_interval = 4
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    # open the baseline DataFrame if it exists
    filename = baseline_path + baseline_file
    if os.path.isfile(filename):
        f = open(filename, 'r')
        baseline = Datafile(f).df
    else:
        baseline = pd.DataFrame()

    if not args.datafile:
        list_of_events = glob.glob(events_path + '*.csv') # * means all if need specific format then *.csv
        latest_event = max(list_of_events, key=os.path.getctime)
        args.datafile = [open(latest_event, 'r')]

    if args.fix:
        for f in args.datafile:
            mydata = Datafile(f, recalculate_co2 = True)

            filename = "/home/pi/event-temp/" + mydata.internname
            header = mydata.internname + "\n" + mydata.rawdata + "\n" + ",".join(mydata.keys) + "\n" + ",".join(mydata.units) + "\n"            
            with open(filename, 'w') as fw:
                fw.write(header)
                mydata.df.to_csv(fw, index=False, header=False)
                fw.close()
            
    elif args.zero:

        filename = create_baseline_file(files=args.datafile, baseline_path=baseline_path, baseline_file=baseline_file)

        # Reopen newly created file for plotting
        f = open(filename, 'r')
        mydata = Datafile(f, output_path = baseline_path)
        if args.tplot:
            mydata.create_dualplot(style=plot_style, format=plot_format, y1err=True, y2err=True, error_interval = error_interval)
        else:
            mydata.create_plot(style=plot_style, format=plot_format, err=True, error_interval = error_interval)

    else:
        for f in args.datafile:
            mydata = Datafile(f, output_path = output_path)
            if 'dtc' in baseline:
                mydata.add_baseline(baseline = baseline)
            print mydata.results
            if args.tplot:
                mydata.create_dualplot(style=plot_style, format=plot_format)
            else:
                mydata.create_plot(style=plot_style, format=plot_format)
