#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parse
import sys, time, os, glob

import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from log import log_message

import re # for string parsing

import itertools

import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import matplotlib.animation as animation
#print(plt.style.available)

from fit import my_fit, _1gauss
from event_list import get_newest_events

def replace_in_list(a, old, new):
    for n, i in enumerate(a):
        if i == old:
            a[n] = new
    return a

class Datafile(object):
    def __init__(self, datafile, output_path = 'data/events/graph/', recalculate_co2 = False, tmax=0, npeak = 5): # datafile is a valid filepointer
        
        #init data structure
        self.datastring = ""
        self.tmax       = tmax # time period in seconds used to integrate
        self.datafile   = datafile.name
        self.outputDir  = output_path
        self.date       = time.strftime("%Y-%m-%d")
        skip_rows       = 3
        header          = 2
        self.internname = datafile.readline().rstrip('\n') # first line contains the original filename
        self.rawdata    = datafile.readline().rstrip('\n') # second line points to raw data
        self.fit_coeff  = [] # variable to hold the fitting results
        self.npeak      = npeak # number of fitted gausian curves (must identical in Results object)

        #print >>sys.stderr, "loading: {}".format(datafile.name)

        # search for the serial number
        # first test if data was taken at JFJ 
        self.sn = re.findall(r'(JFJ-SN\d+.)', self.rawdata)
        if not self.sn:
            self.sn = re.findall(r'(SN\d+.)', self.rawdata)
        if self.sn:
            self.sn = self.sn[-1][:-1]

        # for back compatibility, the next 4 lines will be tested to see if the event
        # includes also information about sampling volume and volume weigthed co2
        temp            = [] # for testing lines
        for i in range(4):
            temp.append(datafile.readline().rstrip('\n\r'))
        try:
            # added 11.07.2020: checking for label instead of number to avoid errors when volume is zero
            label = temp[0].split(' ')[0]
            self.volume = float(temp[0].split(' ')[1])
            #if self.volume > 0:
            if label == "volume:":
                if self.volume <= 0:
                    log_message('Warning: volume variable in event is {:.0f}, ignoring the volume value'.format(self.volume))
                    self.volume = False
                try:
                    self.sample_co2 = float(temp[1].split(' ')[1])
                    if self.sample_co2 >= 0:
                        #print >>sys.stderr, 'Using vol. weigthed co2 data found in file: {:.0f} ppm'.format(self.co2)
                        skip_rows += 2
                        header    += 2
                        self.keys  = temp[2].replace(" ","").split(',')
                        self.units = temp[3].replace(" ","").split(',')
                except:
                    self.keys  = temp[1].replace(" ","").split(',')
                    self.units = temp[2].replace(" ","").split(',')
                    skip_rows += 1
                    header    += 1
                    self.sample_co2 = False
        except:
            self.keys  = temp[0].replace(" ","").split(',')
            self.units = temp[1].replace(" ","").split(',')
            self.volume = False
            self.sample_co2 = False
        #print >>sys.stderr, "keys: {}".format(self.keys)

        # Use TeX notation :-)
        self.units = replace_in_list(self.units, 'ug-C', r'$\mu$g-C')
        self.units = replace_in_list(self.units, 'degC', r'$^\circ$C')
        self.units = replace_in_list(self.units, 'ug/min', r'$\mu$g-C/min')

        datafile.seek(0, 0)
        self.df = pd.read_csv(datafile, header=[header], skiprows=[skip_rows])      # loads the datafile
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
            "tc-baseline",
            "tc concentration",
            "sample"
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
        if 'dtc-baseline' in self.df:
            tc_corrected = round(np.trapz(self.tc_df['dtc-baseline'], x=self.tc_df['elapsed-time'])/60, 3)
            print "tc_corrected = {}, volume = {}".format(tc_corrected, self.volume)
            if self.volume:
                concentration = round(tc_corrected/self.volume, 2)
            else:
                concentration = '-'
        else:
            tc_corrected = '-'
            concentration = '-'
        self.results = {
            "date": self.extract_date(),
            "time": self.df['time'][0] if 'time' in self.df else '-',
            "runtime": self.df['runtime'][0] if 'runtime' in self.df else '-',
            "co2-base": round(self.df['co2'].mean() - self.df['co2-event'].mean(), 2),
            "maxtemp": max(self.df['toven']),
            "tc": round(np.trapz(self.tc_df['dtc'], x=self.tc_df['elapsed-time'])/60, 3),
            "tc-baseline": tc_corrected,
#            "tc-baseline": round(np.trapz(self.tc_df['dtc-baseline'], x=self.tc_df['elapsed-time'])/60, 3) if 'dtc-baseline' in self.df else '-'
            "tc concentration": concentration, 
            "sample": self.volume if self.volume else '-',
            "sample co2": self.sample_co2 if self.sample_co2 else '-'
            }
        self.result_units = {
            "date": 'yyyy-mm-dd',
            "time": 'hh:mm:ss',
            "runtime": 's',
            "co2-base": 'ppm',
            "maxtemp": r'$^\circ$C',
            "tc": r'$\mu$g-C',
            "tc-baseline": r'$\mu$g-C',
            "tc concentration": r'$\mu$g-C/m$^3$',
            "sample": r'm$^3$',
            "sample co2": 'ppm'
            }
        
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.datafile)

    def __str__(self):
        tc_concentration = self.results["tc concentration"]
        tc_corrected = self.results["tc-baseline"]
        if tc_corrected == "-":
            tc_str = "TC={:.2f} {}".format(self.results["tc"], self.result_units["tc"])
        else:
            tc_str = "TC-Baseline={:.2f} {}".format(tc_corrected, self.result_units["tc-baseline"])
        if tc_concentration == "-":
            tc_concentration_str = ""
        else:
            tc_concentration_str = " ({} {})".format(tc_concentration, self.result_units["tc concentration"])
        return "FATCAT {} ({} {}): {}{}".format(self.sn, self.results["date"], self.results["time"],
                                                   tc_str, tc_concentration_str)
                                                                    

    def extract_date(self):
        date = self.internname[:10]
        try: 
            parse(date, fuzzy=False)
            return date

        except ValueError:
            return '-'

    def add_baseline(self, baseline, fit = False, p0=False):
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

            if self.volume:
                self.results.update({
                    "tc concentration": round(self.results["tc-baseline"]/self.volume, 2)
                    })

            # fit the data
            if fit:
                print "fitting event {}".format(self.datafile)
                try:
                    self.keys.append('fitted data') # add a new column with the baseline values
                    self.units.append(r'$\mu$g-C/min')
                    self.df['fitted data'], self.fit_coeff, self.r_squared = my_fit(self.df['elapsed-time'],
                                                                                    self.df['dtc-baseline'],
                                                                                    p0 = p0, npeaks = self.npeak)
                except Exception as err:
                    log_message("error fitting the event: {}".format(err))
                    self.df['fitted data'] = np.nan
                    self.r_squared = np.nan
                    self.fit_coeff = []
                    coeffDict = {
                        "A": np.nan,
                        "xc" : np.nan,
                        "sigma" : np.nan,
                        "AStDevErr": np.nan,
                        "xcStDevErr" : np.nan,
                        "sigmaStDevErr" : np.nan
                        }
                    for n in range(self.npeak):
                        self.fit_coeff.append(coeffDict)
                else:
                    #print >>sys.stderr, "----fitted {}, r-squared = {}".format(self.datafile, round(self.r_squared, 4))
                    coeff_string = "----fitted, r-squared = {}, ".format(round(self.r_squared, 4))
                    for num, coeff_list in enumerate(self.fit_coeff):
                        coefficient_name = "A{}".format(num)
                        coeff_string += coefficient_name + "={} ".format(round(coeff_list['A'], 2))
                    print coeff_string

    def create_plot(self, x='elapsed-time', y='dtc', y2='dtc-baseline', style='ggplot', format='svg',
                    err=False, error_interval = 4, mute = False, axeslabel={}, legend={},
                    fitComponents = [], xmax = False, ymax = False):

        plt.style.use('ggplot')

        # introduces a different name for the plotted curves
        if 'y' in legend:
            yname = legend['y']
        else:
            yname = y
        if 'y2' in legend:
            y2name = legend['y2']
        else:
            y2name = y2

        plot = plt.figure()
        if err:
            yerr = y + "-sd"
            plt.errorbar(self.df[x], self.df[y], yerr=self.df[yerr], errorevery=error_interval)
        else:
            plt.plot(self.df[x], self.df[y])
            if y2 in self.df:
                plt.plot(self.df[x], self.df[y2])
                plt.legend((yname, y2name), loc='upper right')

        # add individual fitted components
        for c in fitComponents:
            #plt.plot(self.df[x], c)
            plt.fill_between(self.df[x], c, alpha = 0.5)

        # set ayis labels
        if 'x' in axeslabel:
            xlabel = axeslabel['x'] + ' (' + self.units[self.keys.index(x)] + ')'
        else:
            xlabel = x + ' (' + self.units[self.keys.index(x)] + ')'
        if 'y' in axeslabel:
            ylabel = axeslabel['y'] + ' (' + self.units[self.keys.index(y)] + ')'
        else:
            ylabel = y + ' (' + self.units[self.keys.index(y)] + ')'

        # set nicer limits
        if not xmax:
            xmax = self.df[x].max()
        plt.xlim(self.df[x].min(), xmax)
        if ymax:
            #ymax = self.df[y].max()
            plt.ylim(self.df[y].min(), ymax)
            plt.ylim(0, ymax)
        plt.title(self.internname)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if len(fitComponents) > 0:
           type_of_plot = "_{}components".format(len(fitComponents))
        else:
            type_of_plot = ""
        #filename = (self.outputDir + self.internname.replace('.','_') + '_' + y + type_of_plot + '.' + format).replace(' ','_')
        filename = ("{}_{}{}.{}".format(self.internname.replace('.','_'), y, type_of_plot, format)).replace(' ','_')
        plot.canvas.set_window_title(filename)
        filename = self.outputDir + filename
        plt.savefig(filename)
        if not mute:
            plt.show()
        plt.close(plot)

    def create_dualplot(self, x='elapsed-time', y1='toven', y2='dtc', y3='dtc-baseline',
                        style='ggplot', format='svg', y1err=False, y2err=False, error_interval = 4, mute = False,
                        legend={}, axeslabel={}, fitComponents = [], xmax = False, y1max = False, y2max = False):

        plt.style.use('ggplot')

        # introduces a different name for the plotted curves
        if 'y2' in legend:
            y2name = legend['y2']
        else:
            y2name = y2
        if 'y3' in legend:
            y3name = legend['y3']
        else:
            y3name = y3

        # get units for axis
        unity1 = self.units[self.keys.index(y1)]
        unity2 = self.units[self.keys.index(y2)]
        unitx = self.units[self.keys.index(x)]

        if 'x' in axeslabel:
            xlabel = axeslabel['x'] + ' (' + unitx + ')'
        else:
            xlabel = x + ' (' + unitx + ')'
        if 'y1' in axeslabel:
            ylabel1 = axeslabel['y1'] + ' (' + unity1 + ')'
        else:
            ylabel1 = y1 + ' (' + unity1 + ')'
        if 'y2' in axeslabel:
            ylabel2 = axeslabel['y2'] + ' (' + unity2 + ')'
        else:
            ylabel2 = y2 + ' (' + unity2 + ')'
        

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
        if y1max:
            ax1.set_ylim(limY1min - extra_space1, y1max)
        else:
            ax1.set_ylim(limY1min - extra_space1, limY1max + extra_space1)
        try:
            if y2max:
                ax2.set_ylim(limY2min - extra_space2, y2max)
            else:
                ax2.set_ylim(limY2min - extra_space2, limY2max + extra_space2)
        except:
            # catch error if, e.g., fit procedure failed
            log_message('failed to set limit values for {} curve'.format(y2))
##            if y3 in self.df:
##                limY2min = self.df[y3].min()
##                limY2max = self.df[y3].max()
##                ax2.set_ylim(limY2min - extra_space2, limY2max + extra_space2)
        for ax in [ax1, ax2]:
            if not xmax:
                xmax = self.df[x].max()
            ax.set_xlim(self.df[x].min(), xmax)

        # some formating
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
                ax2.legend((y2name, y3name), loc='upper right')

        # add individual fitted components
        for c in fitComponents:
            #ax2.plot(self.df[x], c)
            ax2.fill_between(self.df[x], c, alpha = 0.5)

        if len(fitComponents) > 0:
           type_of_plot = "_{}components".format(len(fitComponents))
        else:
            type_of_plot = ""

        filename = ("{}_{}_{}{}.{}".format(self.internname.replace('.','_'), y1, y2, type_of_plot, format)).replace(' ','_')
        dualplot.canvas.set_window_title(filename)
        #filename = (self.outputDir + self.internname.replace('.','_') + '_' + y1 + '_' + y2 + type_of_plot + '.' + format).replace(' ','_')
        filename = self.outputDir + filename
        plt.savefig(filename)
        if not mute:
            plt.show()
        plt.close(dualplot)

class ResultsList(object):
    def __init__(self, npeak = 5):
        # create a dataframe to hold results and a list for the units
        self.summary = pd.DataFrame()
        self.summary_keys = []
        self.summary_units = []
        self.files = []
        self.n = 0
        self.npeak = npeak # number of fitted gausian curves

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

        # CREATE a DataFrame to Hold fitted coefficients
        self.fit_coeff_keys = ['date', 'time', 'sample']
        self.fit_coeff_units = ['yyyy-mm-dd', 'hh:mm:ss', r'm$^3$']
        self.coeff = ['A',
                      'AStDevErr',
                      'xc',
                      'xcStDevErr',
                      'sigma',
                      'sigmaStDevErr']
        self.coef_units_dict = {
            'A': r'$\mu$g-C',
            'xc': 's',
            'sigma': 's',
            'AStDevErr': r'$\mu$g-C',
            'xcStDevErr': 's',
            'sigmaStDevErr': 's'
            }
        self.coef_units_decimals = {
            'A': 2,
            'xc': 1,
            'sigma': 1,
            'AStDevErr': 3,
            'xcStDevErr': 2,
            'sigmaStDevErr': 2
            }
        self.average_df_decimals = {
            'elapsed-time': 1,
            'toven': 1,
            'pco2': 1,
            'co2': 1,
            'flow': 2,
            'countdown': 1,
            'co2-event': 3,
            'dtc': 3
            }
        self.default_decimals = 3
        for n in range(self.npeak):
            for c in self.coeff:
                self.fit_coeff_keys.append('{}{}'.format(c,n))
                self.fit_coeff_units.append(self.coef_units_dict[c])
        self.fit_coeff_keys.append('r-squared')
        self.fit_coeff_units.append('-')
        self.coeff_df = pd.DataFrame(columns=self.fit_coeff_keys)

    def _append_coeff(self, coeff_dict, r_squared = False):
        newDict = {
            'date':   self.summary["date"].iloc[-1] ,
            'time':   self.summary["time"].iloc[-1],
            'sample': self.summary["sample"].iloc[-1]
            }
        for n in range(self.npeak):
            for c in self.coeff:
                newDict['{}{}'.format(c,n)] = round(coeff_dict[n][c], self.coef_units_decimals[c])
        newDict['r-squared'] = round(r_squared, 4)
        
        self.coeff_df = self.coeff_df.append(newDict, ignore_index = True)
        
    def append_event(self, datafile):
        self.files.append(datafile.internname.rstrip('\r'))
        
        if self.summary.empty:
            # update columns if baseline corrected column exists
            if 'dtc-baseline' in datafile.df:
                self.average_keys.append('dtc-baseline')
                self.sd_keys.append('dtc-baseline' + '-sd')
                self.all_keys.append('dtc-baseline')
                self.all_keys.append('dtc-baseline' + '-sd')
                if 'fitted data' in datafile.df:
                    self.average_keys.append('fitted data')
                    self.sd_keys.append('fitted data' + '-sd')
                    self.all_keys.append('fitted data')
                    self.all_keys.append('fitted data' + '-sd')
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

        if 'fitted data' in datafile.df:
            self._append_coeff(datafile.fit_coeff, datafile.r_squared)
        
        self.n = self.n + 1

    def build_average_df(self):
        by_row_index = self.df_concat.groupby(self.df_concat.index)
        df_means = by_row_index.mean()
        df_stds = by_row_index.std()

        df = pd.DataFrame(columns=self.all_keys)
        for k in df_means:
            if k in self.average_df_decimals:
                digits = self.average_df_decimals[k]
            else:
                digits = self.default_decimals
            sdkey = self.sd_keys[self.average_keys.index(k)] # get the relevant sd_key
            df[k] = df_means[k].round(digits)
            df[sdkey] = df_stds[k].round(digits)

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
        limY2min = np.nanmin(self.df_concat[y2])
        limY2max = np.nanmax(self.df_concat[y2])
##        limY2min = self.df_concat[y2].min()
##        limY2max = self.df_concat[y2].max()
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

def box_plot(x, y, units, title, filename, style='ggplot', format='svg', date_format='%Y-%m-%d', xlabel='date'):
    #plt.style.use('ggplot')
    plt.style.use(style)

    # definitions for the axes
    left, width = 0.05, 0.75
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
    ax_scatter.scatter(x, y) #circles
    ax_scatter.plot(x, y)    #lines
    ax_scatter.set(xlabel=xlabel, ylabel=y.name + ' (' + units + ')', title=title)
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
    #ax_scatter.set_xlim((tlim0-extra_t, tlim1+extra_t))
    ax_scatter.set_xlim((tlim0, tlim1))
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

    filename = (filename.replace('.','_') + '_' + y.name + '-boxplot.' + format).replace(' ','_')
    plt.savefig(filename)

    return box

def bubble_plot(xdata, ydata, axisnames, units, title=None, style='ggplot', size = None, color = None, label = None,
                xerror = None, yerror = None, filename="fitted_coefficients_plot", format='svg',
                show_error = False):
    plt.style.use(style)

    plot = plt.figure("scatter plot")
    for n, (x, y, s, c, l, xerr, yerr) in enumerate(itertools.izip_longest(xdata, ydata, size, color, label, xerror, yerror, fillvalue=None)):
        if not l:
            l = "group{}".format(n)
        plt.scatter(x, y, s=s, color=c, alpha=0.3, edgecolors='none', label=l)
        lerr = r'$\sigma_\operatorname{' + l + r'}$'
        if show_error:
            plt.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='none', label=lerr)
    if label:
        plt.legend(loc='lower right')
    plt.grid(True)
    xlabel = '{} ({})'.format(axisnames[0], units[0])
    ylabel = '{} ({})'.format(axisnames[1], units[1])
    ### set some axes values to avoid problems due to large error bars
    # first flatten the list of dataframe vectors into a simple list
    xvalues = pd.DataFrame.from_dict(map(dict,xdata)).values.flatten()
    yvalues = pd.DataFrame.from_dict(map(dict,ydata)).values.flatten()
    plt.xlim((np.nanmin(xvalues)*4/5, np.nanmax(xvalues)*6/5))
    plt.ylim((np.nanmin(yvalues)*4/5, np.nanmax(yvalues)*6/5))
##    plt.xlim((min(xvalues)*4/5, max(xvalues)*6/5))
##    plt.ylim((min(yvalues)*4/5, max(yvalues)*6/5))
    ###
    if title:
        plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    filename = (filename.replace('.','_') + '.' + format).replace(' ','_')
    plt.savefig(filename)

    return plot

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

def create_baseline_file(files, baseline_path, baseline_file, summary_path, tmax=0, npeak = 5):

    # create a ResultsList object to hold the event key data
    results = ResultsList()

    for f in files:
        mydata = Datafile(f, tmax=tmax, npeak = npeak) # output path is not needed because data will not be plotted
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
    box_plot(x = results.summary['date']+' '+results.summary['time'], y = results.summary['tc'], title = 'Baseline data', units = r'$\mu$g-C', filename = filename)
        
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

def read_baseline_dictionary(baseline_path, baseline_filename):
    baseline_dictionary = {}
    baselines = glob.glob(baseline_path + 'SN*/' + baseline_filename)
    keys = map(lambda x: re.findall(r'(/SN\d+/)', x), baselines)
    # add elements from JFJ
    baselines_jfj = glob.glob(baseline_path + 'JFJ-SN*/' + baseline_filename)
    baselines += baselines_jfj
    keys += map(lambda x: re.findall(r'(/JFJ-SN\d+/)', x), baselines_jfj)
    # construct the dictionary
    for k, p in zip(keys, baselines):
        if k:
            f = open(p, 'r')
            baseline_dictionary[k[0][1:-1]] = Datafile(f).df
    return baseline_dictionary

if __name__ == "__main__":

    config_file = os.path.abspath(os.path.abspath(os.path.dirname(sys.argv[0])) + "/../config.ini")
    
    parser = argparse.ArgumentParser(description='Graph generator for fatcat event files.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='List of event files to be processed. Leave empty for newest file')
    parser.add_argument("-l", "--last",
                        help="Latest events to consider, must be larger than 1 (e.g., 10files, 5days, 72hours). Overrides 'datafile'.",
                        dest='LAST', type=get_newest_events)
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
    parser.add_argument('--fit', dest='fit', help='Fit gaussian functions to data', action='store_true')
    parser.add_argument('--show-fit-error', dest='ferror', help='Show fit error on bubble graph', action='store_true')
    parser.add_argument('--fix-co2', dest='fix', help='fix the co2-event in the event file', action='store_true')
    parser.add_argument('--mute-graphs', dest='mute', help='Do not plot the data to screen', action='store_true')
    parser.add_argument('--fit-components', dest='fitComponents', help='Fit and display individual fitted curves on graph', action='store_true')
    dict_parser = parser.add_mutually_exclusive_group(required=False)
    dict_parser.add_argument('--baseline-dict', dest='basedict', action='store_true',
                            help='Use a baseline dictionary for files from different instruments (default)')
    dict_parser.add_argument('--default-baseline', dest='basedict', action='store_false',
                            help='Use the baseline for all files')
    parser.add_argument('--alt-baseline', required=False, dest='altbaseline',
                        help="Points to an alternative path storing the baseline file.")
    parser.set_defaults(basedict=True)
    parser.add_argument("-p", "--param",
                        help="Plots also an additional parameter (e.g., {})".format("toven, pco2, co2, flow, countdown, co2-event, dtc, elapsed-time, baseline, dtc-baseline"),
                        dest='param')
    
    args = parser.parse_args()

    # activated --fit rutines if --fit-components was selectes 
    if args.fitComponents:
        args.fit = True
    
    config_file = args.INI
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        events_path    = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/'
        output_path    = eval(config['GENERAL_SETTINGS']['EVENTS_PATH']) + '/graph/'
        plot_style     = eval(config['GRAPH_SETTINGS']['PLOT_STYLE'])
        plot_format    = eval(config['GRAPH_SETTINGS']['FILE_FORMAT'])
        error_interval = eval(config['GRAPH_SETTINGS']['ERROR_EVERY'])
        xmax           = eval(config['GRAPH_SETTINGS']['XMAX'])
        ymax           = eval(config['GRAPH_SETTINGS']['YMAX'])
        tempmax        = 810
        baseline_path  = eval(config['DATA_ANALYSIS']['BASELINE_PATH']) + '/'
        baseline_file  = eval(config['DATA_ANALYSIS']['BASELINE_FILE'])
        summary_path   = eval(config['DATA_ANALYSIS']['SUMMARY_PATH']) + '/'
        summary_file   = eval(config['DATA_ANALYSIS']['SUMMARY_FILE'])
        fit_file       = eval(config['DATA_ANALYSIS']['FIT_FILE'])
        npeak          = eval(config['DATA_ANALYSIS']['NPEAK'])
        tmax           = eval(config['DATA_ANALYSIS']['INTEGRAL_LENGTH'])
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
        xmax = False
        ymax = False
        tempmax = False
        log_message('Could not find the configuration file {0}'.format(config_file))
        npeak = 5

    summary_full_path = summary_path + summary_file
    fit_full_path = summary_path + fit_file

    # open the default baseline DataFrame and assigns a baseline dictionary
    # baseline dictionary is used for time series that involve more than one
    # instrument. Dictionary is based on instrument serial number
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
    else:
        default_baseline = pd.DataFrame()

    if args.LAST:
        file_list = args.LAST
        if len(file_list) == 0:
            log_message("No events found.")
            exit()
        args.datafile = map(lambda x: open(x, 'r'), file_list)

    # Get the last event if none is given
    if not args.datafile:
        list_of_events = glob.glob(events_path + '*.csv') # * means all if need specific format then *.csv
        latest_event = max(list_of_events, key=os.path.getctime)
        args.datafile = [open(latest_event, 'r')]

    # create a ResultsList object to hold the event key data
    results = ResultsList(npeak = npeak)

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
            axeslabel = {'y2' : r'$\Delta$TC'}
            mydata.create_dualplot(style=plot_style, format=plot_format, y1err=True, y2err=True,
                                   error_interval = error_interval, axeslabel = axeslabel)
        else:
            axeslabel = {'y' : r'$\Delta$TC'}
            mydata.create_plot(style=plot_style, format=plot_format, err=True,
                               error_interval = error_interval, axeslabel = axeslabel)

    else:
        # if only one file, then show the diagram per default
        if len(args.datafile) == 1 and not args.mute:
               args.individual_plots = True
        # Uses the default first guess for fitting
        p0 = False

        sn = False
        for f in args.datafile:
            mydata = Datafile(f, output_path = output_path, tmax = tmax, npeak = npeak)
            if not sn == mydata.sn:
                sn = mydata.sn
                log_message("Found {} (starting @ {})".format(sn, mydata.datafile))
            # empty holder for individual fitted curves
            components = []
            if mydata.sn in baseline_dictionary:
                baseline_df = baseline_dictionary[mydata.sn]
            else:
                baseline_df = default_baseline
            if 'dtc' in baseline_df:
                box_y = 'tc-baseline'
                mydata.add_baseline(baseline = baseline_df, fit = args.fit, p0=p0)
                # Use current result as starting guess for next fitting iteration
                if args.fit and False:
                    p0 = []
                    for num, coeff_list in enumerate(mydata.fit_coeff):
                        p0.append(coeff_list['A'])
                        p0.append(coeff_list['xc'])
                        p0.append(coeff_list['sigma'])
                if args.fitComponents:
                # generate the fit components curves
                    for num, coeff_list in enumerate(mydata.fit_coeff):
                        # extract data. Need to correct A from ug/sec to ug/min
                        coeff = {'A' : coeff_list['A']*60, 'xc' : coeff_list['xc'], 'sigma' : coeff_list['sigma']}
                        components.append(mydata.df['elapsed-time'].apply(lambda x: _1gauss(x=x, **coeff)))
            else:
                box_y = 'tc'
                args.fit = False
                
            results.append_event(mydata)

            if (args.param and (not args.param in mydata.keys)):
                log_message("Alternative parameter muss be in this list: {}".format(mydata.keys))
                args.param = False
                

            if args.tplot:
                axeslabel = {'y2' : r'$\Delta$TC'}
                if args.fit:
                    legend = {'y2' : "{}-mode fit".format(npeak), 'y3' : 'Signal'}
                    mydata.create_dualplot(y3='dtc-baseline', y2='fitted data', legend = legend, axeslabel = axeslabel,
                                           style=plot_style, format=plot_format, mute = not args.individual_plots,
                                           fitComponents = components, xmax = xmax, y2max = ymax, y1max = tempmax)
                else:
                    legend = {'y2' : "raw".format(npeak), 'y3' : 'baseline corrected'}
                    mydata.create_dualplot(style=plot_style, format=plot_format, mute = not args.individual_plots,
                                           legend = legend, axeslabel = axeslabel, xmax = xmax, y2max = ymax, y1max = tempmax)
            else:
                axeslabel = {'y' : r'$\Delta$TC'}
                if args.fit:
                    legend = {'y' : "{}-mode fit".format(npeak), 'y2' : 'Signal'}
                    mydata.create_plot(y2='dtc-baseline', y='fitted data',
                                       style=plot_style, format=plot_format, mute = not args.individual_plots,
                                       axeslabel = axeslabel, legend = legend, fitComponents = components,
                                       xmax = xmax, ymax = ymax)
                else:
                    legend = {'y' : "raw".format(npeak), 'y2' : 'baseline corrected'}
                    mydata.create_plot(style=plot_style, format=plot_format, mute = not args.individual_plots,
                                       axeslabel = axeslabel, legend = legend,
                                       xmax = xmax, ymax = ymax)

            if args.param:
                mydata.create_dualplot(style=plot_style, format=plot_format, mute = not args.individual_plots,
                                           xmax = xmax, y1max = tempmax, y2 = args.param, y3 = False)


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

        if args.fit:
            header2 = ",".join(results.fit_coeff_keys) + "\n" + ",".join(results.fit_coeff_units) + "\n"
            with open(fit_full_path, 'w') as f:
                f.write(header1)
                f.write(header2)
                results.coeff_df.to_csv(f,index=False, header=False)
                f.close()

            # Generate a bubble plot to study the goodness of the fit
            xdata = []
            ydata = []
            size = []
            xerror = []
            yerror = []
            label = []
            for i in range(results.npeak):
                xdata.append(results.coeff_df['sigma{}'.format(i)])
                xerror.append(results.coeff_df['sigmaStDevErr{}'.format(i)])
                ydata.append(results.coeff_df['xc{}'.format(i)])
                yerror.append(results.coeff_df['xcStDevErr{}'.format(i)])
                size.append(results.coeff_df['A{}'.format(i)]*1000)
                label.append("peak{}".format(i))
            color = ['tab:blue', 'tab:orange', 'tab:green', 'tab:grey', 'tab:olive' ]
            color = color[0 : results.npeak]
            filename = fit_full_path.replace('.','_') + '-FitCoeffPlot'
            bubble_plot(xdata, ydata, axisnames = ["sigma", "xc"], units = ["s", "s"], title="Fitted parameters", size = size, color = color,
                        label = label, xerror = xerror, yerror = yerror,
                        filename = filename, format=plot_format, show_error = args.ferror)
        
        filename = summary_path + summary_file.replace('.','_') + '-boxplot.' + plot_format
        if results.n > 1:
            box_plot(results.summary['date']+' '+results.summary['time'], results.summary[box_y], r'$\mu$g-C', 'Total Carbon', filename, format=plot_format, date_format='%Y-%m-%d %H:%M:%S')
            if not args.mute:
                if args.param:
                    results.animated_plot(y2=args.param)
                elif args.fit:
                    results.animated_plot(y3='dtc-baseline', y2='fitted data')
                else:
                    results.animated_plot()
