#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parse
import time, datetime, os, glob

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#print(plt.style.available)

from plot_event import Datafile, ResultsList, generate_df_stats

def day_plot(df, tc_column = 'tc', filename = "day_overview", title = "Day Overview", style='ggplot', format='svg', mute = False):
    plt.style.use('ggplot')

    # definitions for the axes
    left, width = 0.1, 0.6
    bottom, height = 0.1, 0.25
    spacing = 0.005

    register_matplotlib_converters()
    x = df['date']+' '+df['time']
    x = pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S')

    rect_tc = [left, bottom + 2*(height+ spacing), width, height]
    rect_temp = [left, bottom + height + spacing, width, height]
    rect_co2 = [left, bottom, width, height]
    rect_box = [left + width + spacing, bottom + 2*(height+ spacing), 1 - (2*left + width + spacing), height]

    # start with a rectangular Figure
    overview = plt.figure(title, figsize=(10, 8))

    overview.suptitle(title, fontsize=16)

    ax_tc = plt.axes(rect_tc)
    ax_tc.tick_params(direction='in', top=True, right=True, labelbottom=False)
    ax_temp = plt.axes(rect_temp)
    ax_temp.tick_params(direction='in', top=True, right=True, labelbottom=False)
    ax_co2 = plt.axes(rect_co2)
    ax_co2.tick_params(direction='in', top=True, right=True)
    ax_box = plt.axes(rect_box)
    ax_box.tick_params(direction='in', labelleft=False)

    # the tc plot:
    ax_tc.scatter(x, df[tc_column])
    myFmt = mdates.DateFormatter('%H:%M')
    ax_tc.xaxis.set_major_formatter(myFmt)
    ax_tc.set(xlabel='date', ylabel=tc_column + ' (ug-C)', title="Total Carbon")

    # the temp(erature) plot:
    ax_temp.scatter(x, df['maxtemp'])
    ax_temp.xaxis.set_major_formatter(myFmt)
    ax_temp.set(xlabel='date', ylabel='Temperature (degC)', title="Temperature")

    # the co2 plot:
    ax_co2.scatter(x, df['co2-base'])
    ax_co2.xaxis.set_major_formatter(myFmt)
    ax_co2.set(xlabel='date', ylabel='CO2 baseline (ppm)', title="CO2")

    # now determine nice limits by hand:
    lim0 = df[tc_column].min()
    lim1 = df[tc_column].max()
    templim0 = df['maxtemp'].min()
    templim1 = df['maxtemp'].max()
    colim0 = df['co2-base'].min()
    colim1 = df['co2-base'].max()
    tlim0 = x.min()
    tlim1 = x.max()
    extra_space_tc = (lim1 - lim0)/10
    extra_space_temp = (templim1 - templim0)/10
    extra_space_co2 = (colim1 - colim0)/10
    extra_time = datetime.timedelta(minutes=30)
    ax_tc.set_ylim((lim0-extra_space_tc, lim1+extra_space_tc))
    ax_tc.set_xlim((tlim0-extra_time, tlim1+extra_time))
    ax_temp.set_ylim((templim0-extra_space_temp, templim1+extra_space_temp))
    ax_temp.set_xlim(ax_tc.get_xlim())
    ax_co2.set_ylim((colim0-extra_space_co2, colim1+extra_space_co2))
    ax_co2.set_xlim(ax_tc.get_xlim())

    ax_box.boxplot(df[tc_column])

    ax_box.set_ylim(ax_tc.get_ylim())

    filename = filename.replace('.','_') + '_' + df[tc_column].name + '-day_overview.' + format
    plt.savefig(filename)
    if not mute:
        plt.show()
    else:
        plt.close(box)

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    
    config_file = '../config.ini'
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
        summary_path = eval(config['DATA_ANALYSIS']['SUMMARY_PATH']) + '/'
        summary_file = eval(config['DATA_ANALYSIS']['SUMMARY_FILE'])
        tmax = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
    else:
        events_path   = '~/fatcat-files/data/events/'  # if ini file cannot be found
        output_path   = events_path + 'graph/'
        plot_style    = 'ggplot'
        plot_format   = 'svg'
        baseline_path = '~/fatcat-files/data/baseline/'
        baseline_file = 'zero_event.csv'
        summary_path = '~/fatcat-files/data/baseline/'
        summary_file = 'summary_output.csv'
        tmax = 0
        error_interval = 4
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    parser = argparse.ArgumentParser(description='Generates a visual summary of a day or date interval')
    parser.add_argument("-s", "--startdate", help="The Start Date - format YYYY-MM-DD",
                        dest='START', required=True, type=valid_date)
    
    args = parser.parse_args()

    # open the baseline DataFrame if it exists
    filename = baseline_path + baseline_file
    if os.path.isfile(filename):
        f = open(filename, 'r')
        baseline = Datafile(f).df
        tc_column = 'tc-baseline'
    else:
        baseline = pd.DataFrame()
        tc_column = 'tc'

    # create a ResultsList object to hold the event key data
    results = ResultsList()

    # create the list of events
    date_str = args.START.strftime('%Y-%m-%d')
    filemask = date_str + '-????-eventdata.csv'
    print "Searching files: " + filemask
    for e in glob.glob(events_path + filemask):
        print "Processing: " + e
        with open(e, 'r') as f:
            mydata = Datafile(f, output_path = output_path, tmax = tmax)
            f.close()
            if tc_column == 'tc-baseline':
                mydata.add_baseline(baseline = baseline)
            results.append_event(mydata)

    summary_full_path = summary_path + date_str + "-" + summary_file
            
    # write the results table to the summary file and include the stats in file header
    stats_df = generate_df_stats(results.summary)
    header1 = "Source files:" + " ".join(results.files) + "\n\n"
    header2 = "\n" + ",".join(results.summary_keys) + "\n" + ",".join(results.summary_units) + "\n"
    with open(summary_full_path, 'w') as f:
        f.write(header1)
        stats_df.to_csv(f, index=True, header=True)
        f.write(header2)
        results.summary.to_csv(f, index=False, header=False)
        f.close()

    print stats_df.head()
    print results.summary.tail(20)

    # send summary path, figure will append appropriate data
    day_plot(results.summary, tc_column = tc_column, title = 'Overview: ' + date_str, filename = summary_full_path,
             format=plot_format)
