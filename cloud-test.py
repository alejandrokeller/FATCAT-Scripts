#!/usr/bin/env python

""" Simple http POST example using Python 2.7 and urllib and urllib2."""

import urllib
import urllib2
import ast # for datastring parsing

from collections import namedtuple

public_hash     = '1KqJp77Q34H4zVWgg1Ga'
private_hash    = '02ZEB66VWbSdkM577zAw'
base_url        = 'https://data.sparkfun.com'
post_url        = base_url + '/input/' + public_hash


headers = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Phant-Private-Key': private_hash
}

def httpsend(datastring = "52837	800	22.8	150	23.2	330	328.5	210	204.6	51.1	94.1	446.9	1.00	3.8	0"):

    keys = [
            "runtime",
            "spoven",
            "oventemp",
            "spcoil",
            "tcoil",
            "spband",
            "tband",
            "spcat",
            "cattemp",
            "tco2",
            "pressure",
            "co2",
            "flow",
            "curr",
            "countdown"]
    
    delkeys = [
            "runtime",
            "spoven",
    #        "toven",
            "spcoil",
            "tcoil",
            "spband",
            "tband",
            "spcat",
    #        "tcat",
            "tco2",
    #        "pco2",
    #        "co2",
    #        "flow",
            "curr",
    #        "countdown"
            ]

    datavector = [ast.literal_eval(s) for s in datastring.split( )]
    i = 0
    data = {}
    for k in keys:    
        data[k] = datavector[i]
        i += 1
    
    i = 0
    for k in delkeys:    
        del data[k]
        i += 1
    
    data = urllib.urlencode(data)
    post_request = urllib2.Request(post_url,data,headers)

    #print "This gets the code: ", post_request.header_items()
    #print post_request.get_selector()
    #print post_request.get_host()
    #print post_request.get_type()
    #print post_request.get_full_url()
    #print post_request.get_method()
    print post_request.get_data()

    try:
        post_response = urllib2.urlopen(post_request)
        print post_response.read()
    except urllib2.URLError as e:
        print "URL Error: ", e.reason

if __name__ == "__main__":
	httpsend()
