#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parse
import sys, time, os, glob

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import matplotlib.animation as animation
#print(plt.style.available)

def replace_in_list(a, old, new):
    for n, i in enumerate(a):
        if i == old:
            a[n] = new
    return a

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/', recalculate_co2 = False, tmax=0): # datafile is a valid filepointer
        
        #init data structure
        self.datastring = ""
        self.tmax       = tmax # time period in seconds used to integrate
        self.datafile   = datafile.name
        self.outputDir  = output_path
        self.date       = time.strftime("%Y-%m-%d")
        self.internname = datafile.readline().rstrip('\n') # first line contains the original filename
        self.rawdata    = datafile.readline().rstrip('\n') # second line points to raw data
        self.keys       = datafile.readline().rstrip('\n').replace(" ","").split(',')
        self.units      = datafile.readline().rstrip('\n').replace(" ","").split(',')

        # Use TeX notation :-)
        self.units = replace_in_list(self.units, 'ug-C', r'$\mu$g-C')
        self.units = replace_in_list(self.units, 'degC', r'$^\circ$C')
        self.units = replace_in_list(self.units, 'ug/min', r'$\mu$g-C/min')

        datafile.seek(0, 0)
        self.df = pd.read_csv(datafile, header=[2], skiprows=[3])      # loads the datafile
        datafile.close()
        self.df.columns=self.keys

        if not 'elapsed-time' in self.keys:
            self.keys.append('elapsed-time') # add a new column with the analysis time
            self.units.append('s')
            self.df['elapsed-time'] = self.df['runtime']-self.df['runtime'][0]

        ppmtoug = 12.01/22.4 # factor to convert C in ppm to ug/lt at 0 degC and 1atm
        ## recalculate dtc using real time flow instead of the average flow
        #self.df['dtc'] = self.df['co2-event']*self.df['flow']*ppmtoug ### Evaluate TC using real time flow
        if recalculate_co2:
            ## recalculate co2-event using the (mean) flow and dtc
            self.df['co2-event'] = self.df['dtc']/(self.df['flow'].mean()*ppmtoug) ### Evaluate TC using (mean) flow
            self.df['co2-event'] = round(self.df['co2-event'], 1)
            self.df['dtc'] = round(self.df['dtc'], 3)

        # create event results Dictionary
        self.result_keys = [
            "date",
            "time",
            "runtime",
            "co2-base",
            "maxtemp",
            "tc",
            "tc-baseline"
            ]

        # Create a subset of the DataFrame and load data up to the desired integral time
        self.tc_keys = ['elapsed-time', 'dtc']
        if 'dtc-baseline' in self.df:
            tc_keys.append('dtc-baseline') 
        if self.tmax == 0:
            self.tc_df = self.df.loc[:,self.tc_keys]
        else:
            self.tc_df = (self.df[(self.df['elapsed-time'] <= self.tmax)])[self.tc_keys]

        # Create the results DataSeries, integrating dtc and, if available, dtc-baseline
        self.results = {
            "date": self.extract_date(),
            "time": self.df['time'][0] if 'time' in self.df else '-',
            "runtime": self.df['runtime'][0] if 'runtime' in self.df else '-',
            "co2-base": round(self.df['co2'].mean() - self.df['co2-event'].mean(), 2),
            "maxtemp": max(self.df['toven']),
            "tc": round(np.trapz(self.tc_df['dtc'], x=self.tc_df['elapsed-time'])/60, 3),
            "tc-baseline": round(np.trapz(self.tc_df['dtc-baseline'], x=self.tc_df['elapsed-time'])/60, 3) if 'dtc-baseline' in self.df else '-'
            }
        self.result_units = {
            "date": 'yyyy-mm-dd',
            "time": 'hh:mm:ss',
            "runtime": 's',
            "co2-base": 'ppm',
            "maxtemp": r'$^\circ$C',
            "tc": r'$\mu$g-C',
            "tc-baseline": r'$\mu$g-C'
            }

    def extract_date(self):
        date = self.internname[:10]
        try: 
            parse(date, fuzzy=False)
            return date

        except ValueError:
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
            self.tc_keys = ['elapsed-time', 'dtc', 'dtc-baseline']
            if self.tmax == 0:
                self.tc_df = self.df.loc[:,self.tc_keys]
            else:
                self.tc_df = (self.df[(self.df['elapsed-time'] <= self.tmax)])[self.tc_keys]
            self.results["tc-baseline"] = round(np.trapz(self.tc_df['dtc-baseline'], x=self.tc_df['elapsed-time'])/60,3)

    def create_plot(self, x='elapsed-time', y='dtc', y2='dtc-baseline', style='ggplot', format='svg', err=False, error_interval = 4, mute = False):

        plt.style.use('ggplot')

        plot = plt.figure()
        if err:
            yerr = y + "-sd"
            plt.errorbar(self.df[x], self.df[y], yerr=self.df[yerr], errorevery=error_interval)
        else:
            plt.plot(self.df[x], self.df[y])
            if y2 in self.df:
                plt.plot(self.df[x], self.df[y2])
                plt.legend((y, y2), loc='upper right')
        xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        ylabel = y + ' (' + self.units[self.keys.index(y)] + ')'
        plt.xlim(self.df[x].min(), self.df[x].max())
        plt.title(self.internname)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        filename = self.outputDir + self.internname.replace('.','_') + '_' + y + '.' + format
        plt.savefig(filename)
        if not mute:
            plt.show()
        plt.close(plot)

    def create_dualplot(self, x='elapsed-time', y1='toven', y2='dtc', y3='dtc-baseline',
                        style='ggplot', format='svg', y1err=False, y2err=False, error_interval = 4, mute = False):

        plt.style.use('ggplot')

        # definitions for the axes
        spacing = 0.01

        # create a figure with two subplots
        dualplot, (ax1, ax2) = plt.subplots(2,1)
        dualplot.subplots_adjust(wspace=spacing, hspace=spacing)
        ax1.tick_params(direction='in', labelbottom=False)

        # the same axes initalizations as before (just now we do it for both of them)
        # now determine nice limits by hand:
        limY1min = self.df[y1].min()
        limY1max = self.df[y1].max()
        limY2min = self.df[y2].min()
        limY2max = self.df[y2].max()
        extra_space1 = (limY1max - limY1min)/10
        extra_space2 = (limY2max - limY2min)/10
        ax1.set_ylim(limY1min - extra_space1, limY1max + extra_space1)
        ax2.set_ylim(limY2min - extra_space2, limY2max + extra_space2)
        for ax in [ax1, ax2]:
            ax.set_xlim(self.df[x].min(), self.df[x].max())

        # some formating
        unity1 = self.units[self.keys.index(y1)]
        unity2 = self.units[self.keys.index(y2)]
        unitx = self.units[self.keys.index(x)]
        ylabel1 = y1 + ' (' + unity1 + ')'
        ylabel2 = y2 + ' (' + unity2 + ')'
        xlabel = x + ' (' + unitx + ')'
        ax1.set_ylabel(ylabel1)
        ax2.set_ylabel(ylabel2)
        ax2.set_xlabel(xlabel)
        ax1.set_title(self.internname)

        if y1err:
            yerr = y1 + "-sd"
            ax1.errorbar(self.df[x], self.df[y1], yerr=self.df[yerr], errorevery=error_interval)
        else:
            ax1.plot(self.df[x], self.df[y1])

        if y2err:
            yerr = y2 + "-sd"
            ax2.errorbar(self.df[x], self.df[y2], yerr=self.df[yerr], errorevery=error_interval)
        else:
            if y2 in self.df:
                ax2.plot(self.df[x], self.df[y2])
            if y3 in self.df:
                ax2.plot(self.df[x], self.df[y3])
                ax2.legend((y2, y3), loc='upper right')

        filename = self.outputDir + self.internname.replace('.','_') + '_' + y1 + '_' + y2 + '.' + format
        plt.savefig(filename)
        if not mute:
            plt.show()
        plt.close(dualplot)

class ResultsList(object):
    def __init__(self):
        # create a dataframe to hold results and a list for the units
        self.summary = pd.DataFrame()
        self.summary_keys = []
        self.summary_units = []
        self.files = []
        self.n = 0

        # CREATE a DataFrame to Hold the mean value.
        self.average_keys = [
            'elapsed-time',
            'toven',
            'pco2',
            'co2',
            'flow',
            'countdown',
            'co2-event',
            'dtc'
            ]

        # CREATE keys for stand. dev. and final csv file
        self.sd_keys   = [] # column names with appended "-sd"
        self.all_keys  = [] # column names followed by name with appended "-sd"
        self.all_units = [] # units list for all_keys columns
        for k in self.average_keys:
            self.sd_keys.append(k + '-sd')
            self.all_keys.append(k)
            self.all_keys.append(k + '-sd')
    
        self.df_list = [] # create a list object to hold the DataFrames

        # CREATE a DataFrame to hold the final csv data file
        self.df_concat = pd.DataFrame(columns=self.average_keys)
        self.df_list = []

    def append_event(self, datafile):
        self.files.append(datafile.internname)
        if self.summary.empty:
            # update columns if baseline corrected column exists
            if 'dtc-baseline' in datafile.df:
                self.average_keys.append('dtc-baseline')
                self.sd_keys.append('dtc-baseline' + '-sd')
                self.all_keys.append('dtc-baseline')
                self.all_keys.append('dtc-baseline' + '-sd')
                self.df_concat = pd.DataFrame(columns=self.average_keys)
            self.summary = pd.DataFrame(columns=datafile.result_keys).append(datafile.results, ignore_index = True)
            self.summary_keys = datafile.result_keys
            for k in self.summary_keys:
                self.summary_units.append(datafile.result_units[k])

            for k in self.average_keys:
                # Create list of units to be exported to average event the CSV-file
                unit = datafile.units[datafile.keys.index(k)]
                self.all_units.append(unit)
                self.all_units.append(unit)

        else:
            self.summary = self.summary.append(datafile.results, ignore_index = True)
        
        # Extract relevant information for the mean dataframe
        subset_df = pd.DataFrame(columns=self.average_keys)
        for k in self.average_keys:
            subset_df[k] = datafile.df[k]

        # concatenate them
        self.df_list.append(subset_df)
        self.df_concat = pd.concat((self.df_concat, subset_df))
        
        self.n = self.n + 1

    def build_mean(self):
        by_row_index = self.df_concat.groupby(self.df_concat.index)
        df_means = by_row_index.mean()

        return df_means

    def build_sd(self):
        by_row_index = self.df_concat.groupby(self.df_concat.index)
        df_stds = by_row_index.std()

        return df_stds

    def build_average_df(self):
        by_row_index = self.df_concat.groupby(self.df_concat.index)
        df_means = by_row_index.mean()
        df_stds = by_row_index.std()

        df = pd.DataFrame(columns=self.all_keys)
        for k in df_means:
            sdkey = self.sd_keys[self.average_keys.index(k)] # get the relevant sd_key
            df[k] = df_means[k]
            df[sdkey] = df_stds[k]

        return df

    def animated_plot(self, x='elapsed-time', y1='toven', y2='dtc', y3='dtc-baseline',
                        style='ggplot'):

        plt.style.use('ggplot')

        # definitions for the axes
        spacing = 0.01

        # create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2,1)
        fig.subplots_adjust(wspace=spacing, hspace=spacing)
        # intialize two line objects (one in each axes)
        line1, = ax1.plot([], [])
        line2, = ax2.plot([], [])
        line3, = ax2.plot([], [])
        line = [line1, line2, line3]
        ax1.tick_params(direction='in', labelbottom=False)

        # the same axes initalizations as before (just now we do it for both of them)
        # now determine nice limits by hand:
        limY1min = self.df_concat[y1].min()
        limY1max = self.df_concat[y1].max()
        limY2min = self.df_concat[y2].min()
        limY2max = self.df_concat[y2].max()
        extra_space1 = (limY1max - limY1min)/10
        extra_space2 = (limY2max - limY2min)/10
        ax1.set_ylim(limY1min - extra_space1, limY1max + extra_space1)
        ax2.set_ylim(limY2min - extra_space2, limY2max + extra_space2)
        for ax in [ax1, ax2]:
            ax.set_xlim(self.df_concat[x].min(), self.df_concat[x].max())

        # some formating
        unity1 = self.all_units[self.all_keys.index(y1)]
        unity2 = self.all_units[self.all_keys.index(y2)]
        unitx = self.all_units[self.all_keys.index(x)]
        ylabel1 = y1 + ' (' + unity1 + ')'
        ylabel2 = y2 + ' (' + unity2 + ')'
        xlabel = x + ' (' + unitx + ')'
        ax1.set_ylabel(ylabel1)
        ax2.set_ylabel(ylabel2)
        ax2.set_xlabel(xlabel)

        if y3 in self.df_concat:
            ax2.legend((y2, y3), loc='upper right')
            show_y3 = True

        def animate(data):
            i = self.files.index(data)
            ax1.set_title(data)
            xdata = self.df_list[i][x]
            y1data = self.df_list[i][y1]
            y2data = self.df_list[i][y2]
            # update the data of both line objects
            line[0].set_data((xdata, y1data))
            line[1].set_data((xdata, y2data))
            if show_y3:
                y3data = self.df_list[i][y3]
                line[2].set_data((xdata, y3data))

            return line

        ani = animation.FuncAnimation(fig, animate, frames = self.files, interval=0.5*1000)

        plt.show()

def box_plot(x, y, units, title, filename, style='ggplot', format='svg', date_format='%Y-%m-%d'):
    plt.style.use('ggplot')

    # definitions for the axes
    left, width = 0.1, 0.7
    bottom, height = 0.15, 0.75
    spacing = 0.005
    box_width = 1 - (1.5*left + width + spacing)
##    Histogram version    
##    left, width = 0.06, 0.5
##    box_width = (box_width - spacing)/2

    register_matplotlib_converters()
    x = pd.to_datetime(x, format=date_format)

    rect_scatter = [left, bottom, width, height]
    rect_box = [left + width + spacing, bottom, box_width, height]
##    rect_hist = [left + width + 2*spacing + box_width, bottom, box_width, height]

    # start with a rectangular Figure
    box = plt.figure("boxplot", figsize=(12, 6))

    ax_scatter = plt.axes(rect_scatter)
    ax_scatter.tick_params(direction='in', top=True, right=True)
    ax_box = plt.axes(rect_box)
    ax_box.tick_params(direction='in', labelleft=False, labelbottom=False)
##    ax_hist = plt.axes(rect_hist)
##    ax_hist.tick_params(direction='in', labelleft=False)

    # the scatter plot:
    ax_scatter.scatter(x, y)
    ax_scatter.set(xlabel='date', ylabel=y.name + ' (' + units + ')', title=title)
    tdelta = x.max() - x.min()
    my_date_formater(ax_scatter, tdelta)

    # now determine nice limits by hand:
    binwidth = 0.25
    lim0 = y.min()
    lim1 = y.max()
    tlim0 = x.min()
    tlim1 = x.max()
    extra_space = (lim1 - lim0)/10
    extra_t = (tlim1 - tlim0)/10
    ax_scatter.set_xlim((tlim0-extra_t, tlim1+extra_t))
    ax_scatter.set_ylim((lim0-extra_space, lim1+extra_space))

    meanpointprops = dict(marker='D')
    ax_box.boxplot(y, showmeans=True, meanprops=meanpointprops)
    ax_box.set_ylim(ax_scatter.get_ylim())
    mu = y.mean()
    sigma = y.std()
    text = r'$\mu={0:.2f},\ \sigma={1:.3f}$'.format(mu, sigma)
    ax_box.text(1, lim1 + extra_space/2, text, horizontalalignment="center", verticalalignment="center")

##    ax_hist.hist(y, orientation='horizontal')
##    ax_hist.set_ylim(ax_scatter.get_ylim())

    filename = filename.replace('.','_') + '_' + y.name + '-boxplot.' + format
    filename = filename.replace(' ','_')
    plt.savefig(filename)

    return box

##def is_date(string, fuzzy=False):
##    """
##    Return whether the string can be interpreted as a date.
##
##    :param string: str, string to check for date
##    :param fuzzy: bool, ignore unknown tokens in string if True
##    """
##    try: 
##        parse(string, fuzzy=fuzzy)
##        return True
##
##    except ValueError:
##        return False

def create_baseline_file(files, baseline_path, baseline_file, summary_path, tmax=0):

    # create a ResultsList object to hold the event key data
    results = ResultsList()

    for f in files:
        mydata = Datafile(f, tmax=tmax) # output path is not needed because data will not be plotted
        results.append_event(mydata)

    header = baseline_file + "\nAverage datafile: " + str(len(results.files)) + " entries:" + " ".join(results.files) + "\n"
    header = header + ",".join(results.all_keys) + "\n" + ",".join(results.all_units) + "\n"

    filename = baseline_path + baseline_file
    with open(filename, 'w') as f:
        f.write(header)
        results.build_average_df().to_csv(f, index=False, header=False)
        f.close()

    # write the results table to the summary file and include the stats in file header
    stats_df = generate_df_stats(results.summary)
    header1 = "Points used for average file:" + baseline_file + ", tmax=" + str(tmax) + "\nSource files:" + " ".join(results.files) + "\n\n"
    header2 = "\n" + ",".join(results.summary_keys) + "\n" + ",".join(results.summary_units) + "\n"
    with open(summary_path, 'w') as f:
        f.write(header1)
        stats_df.to_csv(f, index=True, header=True)
        f.write(header2)
        results.summary.to_csv(f, index=False, header=False)
        f.close()

    print stats_df.head()
    box_plot(x = results.summary['date'], y = results.summary['tc'], title = 'Baseline data', units = r'$\mu$g-C', filename = filename)
        
    return filename

def generate_df_stats(mydata):
    mydata = mydata.drop(['runtime','time', 'date'], axis=1) # drop unnecesary fields
    stats_df = pd.DataFrame()
    
    stats_df['mean']   = mydata.mean()
    stats_df['std']    = mydata.std()
    stats_df['3*std']  = (3*mydata.std())
    stats_df['median'] = mydata.median()
    stats_df['max']    = mydata.max()
    stats_df['min']    = mydata.min()
    
    stats_df = stats_df.round(2)
    
    return stats_df

def my_date_formater(ax, delta):
    if delta.days < 3:
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%y'))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.grid(True, which='minor')
        ax.tick_params(axis="x", which="major", pad=15)
        if delta.days < 0.75:
            ax.xaxis.set_minor_locator(mdates.HourLocator())
        if delta.days < 1:
            ax.xaxis.set_minor_locator(mdates.HourLocator((0,3,6,9,12,15,18,21,)))
        else:
            ax.xaxis.set_minor_locator(mdates.HourLocator((0,6,12,18,)))
    elif delta.days < 8:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%a %d'))
        ax.xaxis.grid(True, which='minor')
        ax.tick_params(axis="x", which="major", pad=15)
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        ax.set(xlabel='date')
    else:
        xtick_locator = mdates.AutoDateLocator()
        xtick_formatter = mdates.AutoDateFormatter(xtick_locator)
        xtick_formatter.scaled[30.] = FuncFormatter(my_days_format_function)
        xtick_formatter.scaled[1.] = FuncFormatter(my_days_format_function)
        ax.xaxis.set_major_locator(xtick_locator)
        ax.xaxis.set_major_formatter(xtick_formatter)
        ax.set(xlabel='date')

def my_days_format_function(x, pos=None):
     x = mdates.num2date(x)
     if pos == 0:
         fmt = '%b %d\n%Y'
     else:
         fmt = '%b %-d'
     label = x.strftime(fmt)
     return label

if __name__ == "__main__":

    config_file = os.path.abspath(os.path.abspath(os.path.dirname(sys.argv[0])) + "/../config.ini")
    
    parser = argparse.ArgumentParser(description='Graph generator for fatcat event files.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='List of event files to be processed. Leave empty for newest file')
    parser.add_argument('--inifile', required=False, dest='INI', default=config_file,
                        help="Path to configuration file ({} if omitted)".format(config_file))
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
    parser.add_argument('--individual-plots', help='Stop at individual event plots [slow]', action='store_true')
    parser.add_argument('--fix-co2', dest='fix', help='fix the co2-event in the event file', action='store_true')
    
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
        summary_path = eval(config['DATA_ANALYSIS']['SUMMARY_PATH']) + '/'
        summary_file = eval(config['DATA_ANALYSIS']['SUMMARY_FILE'])
        tmax = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
    else:
        events_path   = '~/fatcat-files/data/events/'  # if ini file cannot be found
        output_path   = events_path + 'graph/'
        plot_style    = 'ggplot'
        plot_format   = 'pdf'
        baseline_path = '~/fatcat-files/data/baseline/'
        baseline_file = 'zero_event.csv'
        summary_path = '~/fatcat-files/data/baseline/'
        summary_file = 'summary_output.csv'
        tmax = 0
        error_interval = 4
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)

    summary_full_path = summary_path + summary_file

    # open the baseline DataFrame if it exists
    filename = baseline_path + baseline_file
    if os.path.isfile(filename):
        f = open(filename, 'r')
        baseline = Datafile(f).df
    else:
        baseline = pd.DataFrame()

    # Get the last event if none is given
    if not args.datafile:
        list_of_events = glob.glob(events_path + '*.csv') # * means all if need specific format then *.csv
        latest_event = max(list_of_events, key=os.path.getctime)
        args.datafile = [open(latest_event, 'r')]

    # create a ResultsList object to hold the event key data
    results = ResultsList()

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
        filename = create_baseline_file(files=args.datafile, baseline_path=baseline_path, baseline_file=baseline_file, summary_path = summary_full_path, tmax = tmax)

        # Reopen newly created file for plotting
        f = open(filename, 'r')
        mydata = Datafile(f, output_path = baseline_path)
        if args.tplot:
            mydata.create_dualplot(style=plot_style, format=plot_format, y1err=True, y2err=True, error_interval = error_interval)
        else:
            mydata.create_plot(style=plot_style, format=plot_format, err=True, error_interval = error_interval)

    else:
        # if only one file, then show the diagram per default
        if len(args.datafile) == 1:
               args.individual_plots = True
        for f in args.datafile:
            mydata = Datafile(f, output_path = output_path, tmax = tmax)
            if 'dtc' in baseline:
                mydata.add_baseline(baseline = baseline)
                box_y = 'tc-baseline'
            else:
                box_y = 'tc'
            results.append_event(mydata)

            if args.tplot:
                mydata.create_dualplot(style=plot_style, format=plot_format, mute = not args.individual_plots)
            else:
                mydata.create_plot(style=plot_style, format=plot_format, mute = not args.individual_plots)

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
        
        filename = summary_path + summary_file.replace('.','_') + '-boxplot.' + plot_format
        if results.n > 1:
            box_plot(results.summary['date']+' '+results.summary['time'], results.summary[box_y], r'$\mu$g-C', 'Total Carbon', filename, format=plot_format, date_format='%Y-%m-%d %H:%M:%S')
            results.animated_plot()
