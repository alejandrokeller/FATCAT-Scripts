#!/usr/bin/env python

""" Simple http POST example using Python 2.7 and urllib and urllib2."""

import urllib
import urllib2
import sys

### packages for file upload
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

class Uploader(object):
    def __init__(self):
    
        self.private_hash    = '1KqJp77Q34H4zVWgg1Ga'
        base_url        = 'http://www.kellerperez.com/fatcat'
        self.post_url        = base_url + '/insert.php.old'

        self.headers = {
            'Content-type': 'application/x-www-form-urlencoded'
        }

    def httpsend(self, data):

        data = urllib.urlencode(data)
        post_request = urllib2.Request(self.post_url,data,self.headers)

        # post_request.get_data()

        try:
            post_response = urllib2.urlopen(post_request)
            print >>sys.stderr, post_response.read()
            post_response.close()
        except urllib2.URLError as e:
            print >>sys.stderr, "URL Error: ", e.reason

class FileUploader(object):
    def __init__(self):
    
        base_url        = 'http://www.kellerperez.com/fatcat'
        self.post_url        = base_url + '/insert.php'

    def httpsend(self, data):

        # register the streaming http handlers with urllib2
        register_openers()
        
        datagen, headers = multipart_encode(data)
        post_request = urllib2.Request(self.post_url,datagen,headers)

        # post_request.get_data()

        try:
            post_response = urllib2.urlopen(post_request)
            print >>sys.stderr, post_response.read()
            post_response.close()
        except urllib2.URLError as e:
            print >>sys.stderr, "URL Error: ", e.reason
        except KeyboardInterrupt:
            print >>sys.stderr, "fatcat_uploader: Shutdown request...exiting"
            sys.exit(0)
            # raise

if __name__ == "__main__":

    data = {}
    
    values = [
            "2017.09.18",
            "08:00:07",
            "test_file.txt",
            "115208",
            "246199",
            "7.56",
            "840.3",
            "-11.47"]

    keys = [
            "date",
            "time",
            "datafile",
            "dataindex",
            "runtime",
            "co2base",
            "tempoven",
            "tc"]
            
    i = 0
    for k in keys:
       data[k] = values[i]
       i += 1
            
    myUploader = Uploader()
    myUploader.httpsend(data)
