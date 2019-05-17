#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
import time, os, glob

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
#print(plt.style.available)

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/'): # datafile is a valid filepointer
        
        #init data structure
        self.ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm
        self.datastring = ""
        self.datafile   = datafile.name
        self.csvfile    = datafile
        self.outputDir  = output_path
        self.date       = time.strftime("%Y-%m-%d")
        self.internname = self.csvfile.readline().rstrip('\n') # first line contains the original filename
        self.rawdata    = self.csvfile.readline().rstrip('\n') # second line points to raw data
        self.keys       = self.csvfile.readline().rstrip('\n').replace(" ","").split(',')
        self.units      = self.csvfile.readline().rstrip('\n').replace(" ","").split(',')
        self.csvfile.seek(0, 0)

        self.df = pd.read_csv(self.csvfile, header=[2], skiprows=[3])      # loads the datafile
        self.df.columns=self.keys

        if not 'elapsed-time' in self.keys:
           self.keys.append('elapsed-time') # add a new column with the analysis time
           self.units.append('s')
           self.df['elapsed-time'] = self.df['runtime']-self.df['runtime'][0]

        # some debugging
        # print self.df.head(5)
        # print self.keys
        # print self.units

    def create_plot(self, x='elapsed-time', y='dtc', style='ggplot', format='pdf', err=False, error_interval = 4):
        plt.style.use('ggplot')
        if err:
            yerr = y + "-sd"
            plt.errorbar(self.df[x], self.df[y], yerr=self.df[yerr], errorevery=error_interval)
        else:
            plt.plot(self.df[x], self.df[y])
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y + ' (' + self.units[self.keys.index(y)] + ')'
        plt.title(self.internname)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        filename = self.outputDir + self.internname.replace('.','_') + '_' + y + '.' + format
        plt.savefig(filename)
        plt.show()

    def create_dualplot(self, x='elapsed-time', y1='toven', y2='dtc',
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
            plt.plot(self.df[x], self.df[y2])
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y2 + ' (' + self.units[self.keys.index(y2)] + ')'
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        filename = self.outputDir + self.internname.replace('.','_') + '_' + y1 + '_' + y2 + '.' + format
        plt.savefig(filename)
        plt.show()

    def integrate_tc(self, recalculate_dtc = True):
        
        if recalculate_dtc:
            self.df['dtc'] = self.df['co2-event']*self.df['flow']*self.ppmtoug  ### Evaluate TC using real time flow (noise about 2-4%)
            
        tc = np.trapz(self.df['dtc'], x=self.df['elapsed-time'])/60        ### Integrate using trapezoidal rule
        
        maxT = max(self.df['toven'])

        return tc, maxT

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
    
    for file in files:
        mydata = Datafile(file) # output path is not needed because data will not be plotted
        mydata.integrate_tc()   # recalculate dtc using the real time flow and compute the integral
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

    file_list = baseline_file + "\nAverage datafile: " + str(n) + " entries:" + file_list + "\n" + ",".join(all_keys) + "\n" + ",".join(units_list)

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

    if not args.datafile:
        list_of_events = glob.glob(events_path + '*.csv') # * means all if need specific format then *.csv
        latest_event = max(list_of_events, key=os.path.getctime)
        args.datafile = [open(latest_event, 'r')]

    if args.zero:

        filename = create_baseline_file(files=args.datafile, baseline_path=baseline_path, baseline_file=baseline_file)

        # Reopen newly created file for plotting
        file = open(filename, 'r')
        mydata = Datafile(file, output_path = baseline_path)
        if args.tplot:
            mydata.create_dualplot(style=plot_style, format=plot_format, y1err=True, y2err=True, error_interval = error_interval)
        else:
            mydata.create_plot(style=plot_style, format=plot_format, err=True, error_interval = error_interval)

    else:
        for file in args.datafile:
            mydata = Datafile(file, output_path = output_path)
            if args.tplot:
                mydata.create_dualplot(style=plot_style, format=plot_format)
            else:
                mydata.create_plot(style=plot_style, format=plot_format)
