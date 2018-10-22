# Usage
# `python generate-load-times.py <BEACONURL> 10000 0.5`

import requests
import random
import sys
import argparse
import time

def generateRandomLoadTime():
    return random.randomint(10,10000)

parser = argparse.ArgumentParser()
parser.add_argument("target", help="<http...> the http(s) location to send the GET request")
parser.add_argument("calls", help="the number of HTTP calls to make")
parser.add_argument("delay", help="the time in seconds to delay between calls (ie 0.5 is half a second)")

args = parser.parse_args()
i = 0
s = requests.Session()

while (i < int(args.calls)):
    time.sleep(float(args.delay))
    loadTime = generateRandomLoadTime()
    headers = {'event' : 'load', 'clientid' : 'N/A', 'page' : 'page1.html', 'Referer' : 'BrowserX', 'custom_metric_name' : 'page_load_time', 'custom_metric_int_value' : loadTime }
    r = s.post(args.target + '?call=' + str(i),headers=headers)
    if(r.status_code==200):
        sys.stdout.write( str(i) + "-")
    else:
        sys.stdout.write( str(i) + "---->" + str(r.status_code) + "\n")
    sys.stdout.flush()
    i+=1