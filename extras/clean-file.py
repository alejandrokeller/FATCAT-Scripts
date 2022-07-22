#!/usr/bin/env python

import configparser, argparse        # for argument parsing
import os, sys, glob

def clean_file(filename, print_clean_file = False, skip = 3, tab_count = 23):
    status = False

    with open(filename, 'r') as f:
        f.seek(0, 0)
        head = [next(f) for x in range(skip)]
        if print_clean_file:
            for line in head:
                print line.rstrip('\n')
        
        for line in f:
            line_length = len(line)
            tabs = line.count('\t')
            if tabs <> tab_count:
                status = True
                print >> sys.stderr, "Found {} tabs instead of {}:".format(tabs, tab_count)
                print >> sys.stderr, line
            elif print_clean_file:
                print line.rstrip('\n')

    return status

if __name__ == "__main__":

    base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    # move one up
    base_path = os.path.abspath(os.path.join(base_path, os.pardir))
    #base_path = '/FATCAT-scripts'
    config_file = base_path + '/config.ini'
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        data_path = eval(config['GENERAL_SETTINGS']['DATA_PATH']) + '/'
        data_ext = eval(config['LOGGER']['EXTENSION'])
    else:
        raise ValueError('File \'%s\' is not a valid \'.ini\' file' % config_file)

    parser = argparse.ArgumentParser(description='Cleans FATCAT datafiles.')
    parser.add_argument('datafile', metavar='file', type=argparse.FileType('r'),
                        nargs='*', help='List of datafiles to be processed. Leave empty for newest file')
    print_parser = parser.add_mutually_exclusive_group(required=False)
    print_parser.add_argument('--print', dest='print_clean', action='store_true',
                    help='print clean file to std. output')
    print_parser.add_argument('--mute', dest='print_clean', action='store_false',
                    help='only display lines with errors (default)')
    parser.set_defaults(print_clean=False)

    args = parser.parse_args()

    # Get the last datafile if none is given
    if not args.datafile:
        list_of_datafiles = glob.glob(data_path + '*' + data_ext) # * means all if need specific format then *.csv
        latest_datafile = max(list_of_datafiles, key=os.path.getctime)
##        print >>sys.stderr, "Using file: {}".format(latest_datafile)
        args.datafile = [open(latest_datafile, 'r')]

    for file in args.datafile:
        try:
            clean_file(file.name, print_clean_file = args.print_clean)
        except:
            print >> sys.stderr, "Oops! could not load the file {}".format(file.name)
            raise       
