import configparser, argparse # for argument parsing
import time

import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF

import numpy as np
import pandas as pd

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/'): # datafile is a valid filepointer
        
        #init data structure
        self.datastring = ""
        self.datafile   = datafile.name
        self.csvfile    = datafile
        self.outputDir   = output_path
        self.date       = time.strftime("%Y-%m-%d")
        self.internname = self.csvfile.readline().rstrip('\n') # first line contains the original filename
        self.rawdata    = self.csvfile.readline().rstrip('\n') # second line points to raw data

    def load_df():
        self.df = pd.read_csv(self.eventDir, header=[2,3])
        
        sample_data_table = FF.create_table(df.head())
        filename = self.outputDir + 'sample-data-table'
        py.iplot(sample_data_table, filename=filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Graph generator for fatcat event files.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='?', help='file to be processed. Leave empty for newest file')
    parser.add_argument('--inifile', required=False, dest='INI', default='../config.ini',
                        help='Path to configuration file (../config.ini if omitted)')
    
    args = parser.parse_args()
    
    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        output_path = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/graph/'
    else:
        events_path = '~/fatcat-files/data/events/'  # if ini file cannot be found
        output_path = events_path + 'graph/'
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    with args.datafile as file:
        mydata = Datafile(file, output_path = output_path)
        mydata.load_df()
