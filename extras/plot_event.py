import configparser, argparse # for argument parsing
import time, os, glob

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
#print(plt.style.available)

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/'): # datafile is a valid filepointer
        
        #init data structure
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

        self.keys.append('elapsed-time') # add a new column with the analysis time
        self.units.append('s')
        self.df['elapsed-time'] = self.df['runtime']-self.df['runtime'][0]

        # some debugging
        # print self.df.head(5)
        # print self.keys
        # print self.units

    def create_plot(self, x='elapsed-time', y='dtc', style='ggplot', format='pdf'):
        plt.style.use('ggplot')
        plt.plot(self.df[x], self.df[y])
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y + ' (' + self.units[self.keys.index(y)] + ')'
        plt.title(self.internname)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        filename = self.outputDir + self.internname.replace('.','_') + '_' + y + '.' + format
        plt.savefig(filename)
        plt.show()

    def create_dualplot(self, x='elapsed-time', y1='toven', y2='dtc', style='ggplot', format='pdf'):
        plt.style.use('ggplot')
        
        plt.subplot(2,1,1)
        plt.plot(self.df[x], self.df[y1])
        ylabel = y1 + ' (' + self.units[self.keys.index(y1)] + ')'
        plt.title(self.internname)
        plt.ylabel(ylabel)
        
        plt.subplot(2,1,2)
        plt.plot(self.df[x], self.df[y2])
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y2 + ' (' + self.units[self.keys.index(y2)] + ')'
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        filename = self.outputDir + self.internname.replace('.','_') + '_' + y1 + '_' + y2 + '.' + format
        plt.savefig(filename)
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Graph generator for fatcat event files.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='file to be processed. Leave empty for newest file')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                        help='Path to configuration file (../config.ini if omitted)')
    
    args = parser.parse_args()
    
    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        output_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/graph/'
        plot_style = eval(config['GRAPH_SETTINGS']['PLOT_STYLE'])
        plot_format = eval(config['GRAPH_SETTINGS']['FILE_FORMAT'])
    else:
        events_path = '~/fatcat-files/data/events/'  # if ini file cannot be found
        output_path = events_path + 'graph/'
        plot_style = 'ggplot'
        plot_format = 'pdf'
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    if not args.datafile:
        list_of_events = glob.glob(events_path + '*.csv') # * means all if need specific format then *.csv
        latest_event = max(list_of_events, key=os.path.getctime)
        args.datafile = [open(latest_event, 'r')]

    for file in args.datafile:
        mydata = Datafile(file, output_path = output_path)
#        mydata.create_plot(style=plot_style, format=plot_format)
        mydata.create_dualplot(style=plot_style, format=plot_format)
