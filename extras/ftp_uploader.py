#!/usr/bin/env python
# python script for plotting event files
# The script can also be used for generating an "average" event, e.g., to determine the baseline

import configparser, argparse # for argument parsing
from dateutil.parser import parser
import time, datetime, os, glob, sys
import ftplib

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

if __name__ == "__main__":
    
    
    config_file = os.path.abspath(os.path.dirname(sys.argv[0]) + '/../config.ini')
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        report_path = eval(config['DATA_ANALYSIS']['SUMMARY_PATH']) + '/report/'
        ftp_server = eval(config['FTP']['SERVER'])
        ftp_user = eval(config['FTP']['USER'])
        ftp_pass = eval(config['FTP']['PASS'])
        ftp_home = eval(config['FTP']['HOME']) + '/'
    else:
        print >>sys.stderr, 'Could not find the configuration file {0}'.format(config_file)
        exit()

    parser = argparse.ArgumentParser(description='Uploads report files to an ftp server defined in config.ini')
    parser.add_argument("-s", "--startdate", help="The Start Date - format YYYY-MM-DD",
                        dest='START', type=valid_date)
    parser.add_argument("-e", "--enddate", help="The End Date - format YYYY-MM-DD",
                        dest='END', type=valid_date)
    parser.add_argument("-l", "--last", help="Search for files named latest-* (overrides -s parameter)",
                        dest='LAST', action='store_true')   
    
    args = parser.parse_args()

    if args.LAST:
        filemask = 'latest-*'
        file_list = sorted(glob.glob(report_path + filemask))
        if len(file_list) == 0:
            print >>sys.stderr, "No file found"
            exit()
        else:
            print "{} file(s) found.".format(len(file_list))
    else:
        if not args.START:
            args.START = datetime.datetime.today()
        if not args.END:
            args.END = args.START
        if args.END < args.START:
            raise parser.error("End date is prior to start date")

        # create list of days to explore
        delta = args.END - args.START
        filemask = '*'
        file_list = []
        days_to_show = 0
        for i in range(delta.days + 1):
            day = args.START + datetime.timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            day_list = sorted(glob.glob(report_path + date_str + filemask))
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
            print >>sys.stderr, "No flies found in the desired range: {} to {}".format(args.START.strftime('%Y-%m-%d'), args.END.strftime('%Y-%m-%d'))
            exit()
        print str(len(file_list)) + " files found in the time range: " + date_range

##    print "log to ftp server:" + ftp_server
##    print "using user: " + ftp_user + " and pass: " + ftp_pass
##    print "remote dir: " + ftp_home 
    session = ftplib.FTP(ftp_server,ftp_user,ftp_pass)
    for e in file_list:
        print e
        file = open(e,'rb')                             # file to send
        remote_name = 'STOR ' + ftp_home + os.path.basename(file.name)
        session.storbinary(remote_name, file)     # send the file
        file.close()                                    # close file and FTP
    session.quit()
##        with open(e, 'r') as f:
##            mydata = Datafile(f, output_path = output_path, tmax = tmax)
##            f.close()
##            if tc_column == 'tc-baseline':
##                mydata.add_baseline(baseline = baseline)
##            results.append_event(mydata)

