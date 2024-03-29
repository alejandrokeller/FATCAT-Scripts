#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parser
import time, datetime, os, glob, sys

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib
if not sys.stdout.isatty():
    # runs graphs silently without user interaction
    # used if the script is run as cronjob or if
    # stdout has been redirected
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
#print(plt.style.available)

from plot_event import Datafile, ResultsList, generate_df_stats, my_date_formater, my_days_format_function
from plot_event import box_plot, read_baseline_dictionary
from event_list import get_newest_events
from log import log_message

def day_plot(df, df_list, tc_column = 'tc', filename = "day_overview", title = "Day Overview", style='ggplot',
             format='svg', tmax = False):
    plt.style.use('ggplot')

    # definitions for the axes
    left, width = 0.075, 0.37
    bottom, height = 0.1, 0.20
    spacing = 0.005
    contour_spacing = 0.04

    register_matplotlib_converters()
    x = df['date']+' '+df['time']
    x = pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S')

    rect_tc = [left, bottom + 3*(height+ spacing), width, height]
    rect_p = [left, bottom + 2*(height+ spacing), width, height]
    rect_temp = [left, bottom + height + spacing, width, height]
    rect_co2 = [left, bottom, width, height]
    rect_box = [left + width + spacing, bottom + 3*(height+ spacing), (1 - (2*left + width + spacing))/6, height]
    rect_contour = [left + width + 2*contour_spacing, bottom, 1 - (2*left + width + contour_spacing), 2*height + spacing - contour_spacing]

    # start with a rectangular Figure
    complete_overview = plt.figure(title, figsize=(14, 7))

    complete_overview.suptitle(title, fontsize=16)

    ax_tc = plt.axes(rect_tc)
    ax_tc.tick_params(direction='in', top=True, right=True, labelbottom=False)
    ax_p = plt.axes(rect_p)
    ax_p.tick_params(direction='in', top=True, right=True, labelbottom=False)
    ax_temp = plt.axes(rect_temp)
    ax_temp.tick_params(direction='in', top=True, right=True, labelbottom=False)
    ax_co2 = plt.axes(rect_co2)
    ax_co2.tick_params(direction='in', top=True, right=True)
    ax_box = plt.axes(rect_box)
    ax_box.tick_params(direction='in', labelleft=False, labelbottom=False)
    ax_contour = plt.axes(rect_contour)
    ax_contour.tick_params(direction='in', labelleft=True)

    # the tc plot:
    if tc_column == 'tc':
        tc_title = "Total Carbon (Raw)"
        dtc_column = 'dtc'
        visible = True
    else:
        tc_title = "TC - Baseline"
        dtc_column = 'dtc-baseline'
        visible = False
    ax_tc.plot(x, df[tc_column], '--', x, df[tc_column], 'o')
    ax_tc.set(xlabel='time/date', ylabel=r'TC ($\mu$g-C)')
    my_date_formater(ax_tc, x.max() - x.min())
    ax_tc.get_xaxis().set_visible(False)
    ax_tc.set_title(tc_title, loc = 'right', verticalalignment = 'top', visible = False)
    # the tc boxplot
    ax_box.boxplot(df[tc_column])
    ax_box.set_title('TC Box-Plot', loc='right', visible = visible)
    
    # the temp(erature) plot:
    ax_temp.plot(x, df['maxtemp'], '--', x, df['maxtemp'], 'o')
    ax_temp.set(xlabel='time/date', ylabel=r'Temp. ($^\circ$C)')
    my_date_formater(ax_temp, x.max() - x.min())
    ax_temp.get_xaxis().set_visible(False)
    ax_temp.set_title("Maximum Temperature", loc = 'right', verticalalignment = 'top', visible = False)

    # the [initial] p(ressure) plot:
    ax_p.plot(x, df['p'], '--', x, df['p'], 'o')
    ax_p.set(xlabel='time/date', ylabel=r'P (kPa)')
    my_date_formater(ax_p, x.max() - x.min())
    ax_p.get_xaxis().set_visible(False)
    ax_p.set_title("Initial P", loc = 'right', verticalalignment = 'top', visible = False)

    # the co2 plot:
    ax_co2.plot(x, df['co2-base'], '--', x, df['co2-base'], 'o')
    ax_co2.set(xlabel='time/date', ylabel=r'CO$_2$ Baseline (ppm)')
    my_date_formater(ax_co2, x.max() - x.min())
    ax_co2.set_title(r'CO$_2$ baseline', loc = 'right', verticalalignment = 'top', visible = False)

    # The contourplot
    Xcontour, Ycontour = np.meshgrid(x, df_list[0]['elapsed-time'])
    Zcontour = []
    for i in list(x.index.values):
        row = []
        for j in list(df_list[i]['elapsed-time'].index.values):
            row.append(df_list[i][dtc_column][j])
        Zcontour.append(row)
    Zcontour = map(list, zip(*Zcontour))
    cf = ax_contour.contourf(Xcontour, Ycontour, Zcontour)
    ax_contour.set(xlabel='time/date', ylabel='Time [filter heating] (s)')
    my_date_formater(ax_contour, x.max() - x.min())
    complete_overview.colorbar(cf, ax = ax_contour)
    ax_contour.set_title(r'Total Carbon [$\Delta TC$] ($\mu$g-C/minute)')

    # now determine nice limits by hand:
    lim0 = df[tc_column].min()
    lim1 = df[tc_column].max()
    templim0 = df['maxtemp'].min()
    templim1 = df['maxtemp'].max()
    plim0 = df['p'].min()
    plim1 = df['p'].max()
    colim0 = df['co2-base'].min()
    colim1 = df['co2-base'].max()
    tlim0 = x.min()
    tlim1 = x.max()
    extra_space_tc = (lim1 - lim0)/10
    extra_space_temp = (templim1 - templim0)/10
    extra_space_p = (plim1 - plim0)/10
    extra_space_co2 = (colim1 - colim0)/10
    extra_time = datetime.timedelta(minutes=30)
    ax_tc.set_ylim((lim0-extra_space_tc, lim1+extra_space_tc))
    ax_tc.set_xlim((tlim0-extra_time, tlim1+extra_time))
    ax_temp.set_ylim((templim0-extra_space_temp, templim1+extra_space_temp))
    ax_temp.set_xlim(ax_tc.get_xlim())
    ax_p.set_ylim((plim0-extra_space_p, plim1+extra_space_p))
    ax_p.set_xlim(ax_tc.get_xlim()) 
    ax_co2.set_ylim((colim0-extra_space_co2, colim1+extra_space_co2))
    ax_co2.set_xlim(ax_tc.get_xlim())
    ax_box.set_ylim(ax_tc.get_ylim())
    if tmax:
        ax_contour.set_ylim((0, tmax))
            

    filename = filename.replace('.','_') + '_' + df[tc_column].name + '-day_overview.' + format
    plt.savefig(filename)

    return complete_overview

def simple_day_plot(df, df_list, average_df, tc_column = 'tc', filename = "day_overview",
                    title = "Day Overview", style='ggplot', format='svg', tmax = False):
    plt.style.use('ggplot')

    # definitions for the axes
    left, width = 0.075, 0.55
    bottom, height = 0.1, 0.27
    spacing = 0.02
    contour_spacing = 0.03

    register_matplotlib_converters()
    x = df['date']+' '+df['time']
    x = pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S')

    rect_tc = [left, bottom, width*.971, height]
    rect_temp = [left + width + contour_spacing + spacing,
                 bottom + height + contour_spacing,
                 (1 - (2*left + width + 2*contour_spacing + spacing)),
                 0.85*(2*height + spacing)]
    rect_contour = [left, bottom + height + contour_spacing, width, 0.85*(2*height + spacing)]

    # start with a rectangular Figure
    overview = plt.figure(title, figsize=(10, 7))

    overview.suptitle(title, fontsize=16)

    ax_tc = plt.axes(rect_tc)
    ax_tc.tick_params(direction='in', top=True, right=True)
    ax_temp = plt.axes(rect_temp)
    ax_temp.tick_params(direction='in', top=True, right=True, labelleft=False, labelbottom=True, labelright=True)
    ax_contour = plt.axes(rect_contour)
    ax_contour.tick_params(direction='in', labelleft=True, labelbottom=False)

    # the tc plot:
    if tc_column == 'tc':
        tc_title = "Total Carbon (Raw)"
        dtc_column = 'dtc'
        visible = True
    else:
        tc_title = "TC - Baseline"
        dtc_column = 'dtc-baseline'
        visible = False
    tdelta = x.max() - x.min()
    if tdelta.days < 3:
        ax_tc.plot(x, df[tc_column], '--', x, df[tc_column], 'o')
    else:
        ax_tc.plot(x, df[tc_column], '-')
    ax_tc.set(xlabel='time/date', ylabel=r'Total Carbon ($\mu$g-C)')
    ax_tc.set_title(tc_title, loc = 'right', verticalalignment = 'top', visible = False)
    my_date_formater(ax_tc, tdelta)
    
    # the temp(erature) plot:
    Xtemp = average_df['toven']
    Ytemp = df_list[0]['elapsed-time']
    ax_temp.errorbar(Xtemp, Ytemp, xerr=average_df['toven-sd'], errorevery=4)
    ax_temp.set(xlabel=r'Temperature ($^\circ$C)', ylabel='Time since heating start (s)')
    ax_temp.yaxis.set_label_position("right")
    ax_temp.set_title("Furnace Temp.")

    # The contourplot
##    y_contour_values = df_list[0]['elapsed-time']
    # create a list of all posible 'elapsed-time' values
    y_contour_values = pd.DataFrame()
    for i in df_list:
        if y_contour_values.empty:
            y_contour_values = i['elapsed-time']
        else:
            y_contour_values = pd.merge(y_contour_values, i['elapsed-time'],
                                how='outer', on=['elapsed-time'])
    # rearange relevant columns of the dataframes into reduce_list so
    # that all DataFrames use the same 'elapsed time' values
    reduced_list = []
    for i in df_list:
        temp_df = i[['elapsed-time', dtc_column]]
        temp_df = pd.merge(y_contour_values, temp_df, how='left', on=['elapsed-time'])
        reduced_list.append(temp_df)
    Xcontour, Ycontour = np.meshgrid(x, y_contour_values)
    Zcontour = []
    for i in reduced_list:
        row = []
        for j in i[dtc_column]:
            row.append(j)
        Zcontour.append(row)
    Zcontour = map(list, zip(*Zcontour))
    cf = ax_contour.contourf(Xcontour, Ycontour, Zcontour)
    ax_contour.set(ylabel='Time since heating start (s)')
    ax_contour.set_title(r'Total Carbon [$\Delta TC$] ($\mu$g-C/minute)')
    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at contour_spacing inch.
    divider = make_axes_locatable(ax_contour)
    cax = divider.append_axes("right", size="3%", pad=contour_spacing)
    overview.colorbar(cf, cax = cax)

    # now determine nice limits by hand:
    lim0 = df[tc_column].min()
    lim1 = df[tc_column].max()
    templim0 = Xtemp.min()
    templim1 = Xtemp.max()
    tlim0 = x.min()
    tlim1 = x.max()
    extra_space_tc = (lim1 - lim0)/10
    extra_space_temp = (templim1 - templim0)/10
    extra_time = datetime.timedelta(minutes=30)
    ax_tc.set_ylim((lim0-extra_space_tc, lim1+extra_space_tc))
    ax_tc.set_xlim((tlim0, tlim1))
    if tmax:
        ax_contour.set_ylim((0, tmax))
    ax_temp.set_ylim(ax_contour.get_ylim())
    ax_temp.set_xlim((20, 810))
            

    filename = filename.replace('.','_') + '_' + df[tc_column].name + '-simple_day_overview.' + format
    plt.savefig(filename)

    return overview

def valid_date(s):
    try:
        if s.lower() == 'today':
            return datetime.datetime.today()
        elif s.lower() == 'yesterday':
            return datetime.datetime.today() - datetime.timedelta(days=1)
        else:
            return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    
    
    config_file = os.path.abspath(os.path.dirname(sys.argv[0]) + '/../config.ini')
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path   = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        output_path   = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/graph/'
        plot_style    = eval(config['GRAPH_SETTINGS']['PLOT_STYLE'])
        plot_format   = eval(config['GRAPH_SETTINGS']['FILE_FORMAT'])
        error_interval = eval(config['GRAPH_SETTINGS']['ERROR_EVERY'])
        graphmax      = eval(config['GRAPH_SETTINGS']['XMAX'])
        report_name   = eval(config['GRAPH_SETTINGS']['LATEST_NAME'])
        time_axis     = eval(config['GRAPH_SETTINGS']['DATE_AXIS'])
        baseline_path = eval(config['DATA_ANALYSIS']['BASELINE_PATH']) + '/'
        baseline_file = eval(config['DATA_ANALYSIS']['BASELINE_FILE'])
        summary_path = eval(config['DATA_ANALYSIS']['SUMMARY_PATH']) + '/'
        summary_file = eval(config['DATA_ANALYSIS']['SUMMARY_FILE'])
        tmax = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
        flowrate = float(eval(config['DATA_ANALYSIS']['FLOW_RATE']))
        sampling_time = float(eval(config['DATA_ANALYSIS']['SAMPLING_TIME']))
        sampling_volume = flowrate*sampling_time/1000 # in m3
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
        log_message('Could not find the configuration file {0}'.format(config_file))

    parser = argparse.ArgumentParser(description='Generates a visual summary of a day or date interval')
    parser.add_argument("-s", "--startdate", help="The Start Date - format YYYY-MM-DD (today or yesterday are also valid)",
                        dest='START', type=valid_date)
    parser.add_argument("-e", "--enddate", help="The End Date - format YYYY-MM-DD  (today or yesterday are also valid)",
                        dest='END', type=valid_date)
    parser.add_argument("-l", "--last", help="Latest events to consider, must be larger than 1 (e.g., 10files, 5days, 72hours)",
                        dest='LAST', type=get_newest_events)
    parser.add_argument('--mute-graphs', help='Do not plot the data to screen', action='store_true')
    simple_parser = parser.add_mutually_exclusive_group(required=False)
    simple_parser.add_argument('--skip-simple', dest='simple', action='store_false',
                            help='do not generate simple overview graph')
    simple_parser.add_argument('--plot-simple', dest='simple', action='store_true',
                            help='generate simple overview graph (default)')
    parser.set_defaults(simple=True)
    all_parser = parser.add_mutually_exclusive_group(required=False)
    all_parser.add_argument('--skip-complete', dest='allplots', action='store_false',
                            help='do not generate complete overview graph (with base CO2, etc. (default)')
    all_parser.add_argument('--plot-complete', dest='allplots', action='store_true',
                            help='generate complete overview graph (with base CO2, etc.')
    parser.set_defaults(allplots=False)
    concentration_parser = parser.add_mutually_exclusive_group(required=False)
    concentration_parser.add_argument('--skip-concentration', dest='concentration_plot', action='store_false',
                            help='do not generate the concentration plot(default)')
    concentration_parser.add_argument('--plot-concentration', dest='concentration_plot', action='store_true',
                            help='generate concentration plot based on sampling volume on .ini file')
    parser.add_argument('--alt-baseline', required=False, dest='altbaseline',
                        help="Points to an alternative path storing the baseline file.")
    parser.set_defaults(concentration_plot=False)
    dict_parser = parser.add_mutually_exclusive_group(required=False)
    dict_parser.add_argument('--baseline-dict', dest='basedict', action='store_true',
                            help='Use a baseline dictionary for files from different instruments (default)')
    dict_parser.add_argument('--default-baseline', dest='basedict', action='store_false',
                            help='Use the baseline for all files')
    parser.add_argument('--graph-title', required=False, dest='title',
                        help="Override the default concentration graph title.")
    parser.add_argument('--date-title', required=False, dest='datename',
                        help="Override the default name for the date axis.")
    parser.set_defaults(basedict=True)
    
    
    args = parser.parse_args()

    if not args.START:
        args.START = datetime.datetime.today()
    if not args.END:
        args.END = args.START
    if args.END < args.START:
        raise parser.error("End date is prior to start date")

    if args.title:
        report_name = args.title

    if args.datename:
        time_axis = args.datename 

    if args.LAST:
        file_list = args.LAST
        date_range = "latest"
        if len(file_list) == 0:
            log_message("No events found.")
            exit()
    else:
        # create list of days to explore
        delta = args.END - args.START
        filemask = '-????-eventdata.csv'
        file_list = []
        days_to_show = 0
        for i in range(delta.days + 1):
            day = args.START + datetime.timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            day_list = sorted(glob.glob(events_path + date_str + filemask))
            if day_list:
                # set the first day of the overview
                if not file_list:
                    start_date = date_str
                end_date = date_str
                file_list.extend(day_list)
                days_to_show = days_to_show + 1
        try:
            date_range = (start_date if days_to_show == 1 else start_date + '-' + end_date)
        except:
            log_message("No event flies found (range {} to {})".format(args.START.strftime('%Y-%m-%d'), args.END.strftime('%Y-%m-%d')))
            exit()
        log_message("{} files found (range {})".format(len(file_list), date_range))

    # open the default baseline DataFrame and assigns a baseline dictionary
    # baseline dictionary is used for time series that involve more than one
    # instrument. Dictionary is based on instrument serial number.
    # args.altbaseline is used if the user points to a specific file
    filename = False
    baseline_dictionary = {}
    if args.altbaseline:
        if not args.altbaseline.endswith('/'):
            args.altbaseline = args.altbaseline + '/'
        filename = args.altbaseline + baseline_file
        if os.path.isfile(filename):
            log_message("using alternative baseline file: {}".format(filename))
        else:
            log_message("no alternative baseline found under: {}".format(filename))
            filename = False
    if not filename:
        filename = baseline_path + baseline_file
        if args.basedict:
            baseline_dictionary = read_baseline_dictionary(baseline_path, baseline_file)
    if os.path.isfile(filename):
        f = open(filename, 'r')
        default_baseline = Datafile(f).df
        tc_column = 'tc-baseline'
    else:
        default_baseline = pd.DataFrame()
        tc_column = 'tc'

    # create a ResultsList object to hold the event key data
    results = ResultsList()

    sn = False
    for e in file_list:
        with open(e, 'r') as f:
            mydata = Datafile(f, output_path = output_path, tmax = tmax)
            f.close()
            if not sn == mydata.sn:
                sn = mydata.sn
                log_message("Found {} (starting @ {})".format(sn, mydata.datafile))
            if mydata.sn in baseline_dictionary:
                baseline_df = baseline_dictionary[mydata.sn]
            else:
                baseline_df = default_baseline
            if tc_column == 'tc-baseline':
                mydata.add_baseline(baseline = baseline_df)
            results.append_event(mydata)

    summary_full_path = summary_path + date_range + "-" + summary_file
            
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

    ###### CREATED FOR THE METEOSWISS CAMPAIGN ######
    if args.concentration_plot:
        new_column = 'tc concentration'
        new_units = r'$\mu$g-C/m$^3$'
        report_keys = results.summary_keys
        report_units = results.summary_units
        header_report = ",".join(report_keys) + "\n"
        header_report += ",".join(report_units) + "\n"
        report_df = results.summary
        for idx, row in report_df.iterrows():
            if  report_df.loc[idx,'sample'] == '-':
                report_df.loc[idx,new_column] = (report_df.loc[idx,tc_column]/sampling_volume).round(2)
        report_df[new_column] = pd.to_numeric(report_df[new_column])
        report_full_path = summary_path + "report/" + date_range + "-" + summary_file
        with open(report_full_path, 'w') as f:
            f.write(header_report)
            report_df.to_csv(f, index=False, header=False)
            f.close()
        report_graph = report_full_path
        if not report_name:
            report_name = 'Total Carbon Concentration: ' + date_range
        report_plot = box_plot(x = report_df['date'] + ' ' + report_df['time'], y = report_df[new_column],
                               title = report_name, xlabel = time_axis,
                               units = new_units, filename = report_graph)

    print stats_df.head(8)
    print results.summary.tail(20)

    if len(file_list) > 1:
        # send summary path, figure will append appropriate data
        if args.allplots:
            overview = day_plot(results.summary, results.df_list, tc_column = tc_column, title = date_range, filename = summary_full_path,
                     format=plot_format, tmax = graphmax)
            if args.mute_graphs:
                plt.close(overview)
        if args.simple:
            simple_overview = simple_day_plot(results.summary, results.df_list, tc_column = tc_column, title = 'Overview ' + date_range, filename = summary_full_path,
                     format=plot_format, average_df = results.build_average_df(), tmax = graphmax)
            if args.mute_graphs:
                plt.close(simple_overview)
        if not args.mute_graphs:
            plt.show()
    else:
        log_message("Only one event on that range. Generating simple plot...")
        mydata.create_dualplot(style=plot_style, format=plot_format, mute = args.mute_graphs)
