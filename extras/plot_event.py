import plotly.plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as FF

import numpy as np
import pandas as pd

sys.path.append('../')

def load_df(path):
    df = pd.read_csv('sample-data.csv')

   sample_data_table = FF.create_table(df.head())
   py.iplot(sample_data_table, filename='sample-data-table')
    
    
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
    else:
        events_path = '~/fatcat-files/data/events/'  # if ini file cannot be found
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    with args.datafile as file:
        path = event_path + file
        load_df(path = path)
