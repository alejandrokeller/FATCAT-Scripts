#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parser
import time, datetime, os, glob, sys

from re import findall 

def get_newest_events(value):
    file_list = []
    time_units = ["days","hours","weeks","years","files"]
    
    number = findall(r'^\d+', value )[0]
    text = value[len(number):]
    number = int(number)

    if number <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % number)
    if not (text in time_units):
        raise argparse.ArgumentTypeError("{} is not a valid time unit (use {})".format(text,time_units))
    print "search the last {} {}".format(number, text)

    ### get the relevant path
    config_file = os.path.abspath(os.path.dirname(sys.argv[0]) + '/../config.ini')
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path   = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
    else:
        events_path   = '~/fatcat-files/data/events/'  # if ini file cannot be found
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    # get the newest n files
    filemask = '????-??-??-????-eventdata.csv'
    events = sorted(glob.glob(events_path + filemask))
    if text == "files":
        file_list = events[-number:]
    else:
        # get starting date
        if text == 'days':
            start_date = datetime.datetime.today() - datetime.timedelta(days=number)
        elif text == 'hours':
            start_date = datetime.datetime.today() - datetime.timedelta(hours=number)
        elif text == 'weeks':
            start_date = datetime.datetime.today() - datetime.timedelta(weeks=number)
        elif text == 'years':
            start_date = datetime.datetime.today() - datetime.timedelta(days=365*number)
        print >>sys.stderr, 'Searching from {}'.format(start_date)

        for e in reversed(events):
            event_date = datetime.datetime.strptime(e[-29:-14], '%Y-%m-%d-%H%M')
            if event_date >= start_date:
                file_list.insert(0,e)
            else:
                break
        
    return file_list

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generates a visual summary of a day or date interval')
    parser.add_argument("-l", "--last", help="Latest events to consider, must be larger than 1 (e.g., 10files, 5days, 72hours)",
                        dest='LAST', type=get_newest_events)
    
    args = parser.parse_args()

    if args.LAST:
        file_list = args.LAST
        print >>sys.stderr, "{} files found".format(len(file_list))
        date_range = "latest"
    else:
        print >>sys.stderr, "No files found"
