# Usage
# `python click-burst.py <BEACONURL>`
# Sends 3 'click' events per second for 3 minutes

import requests
import random
import sys
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("target", help="<http...> the http(s) location to send the GET request")

args = parser.parse_args()
i = 0
s = requests.Session()

while (i < 540):
  time.sleep(0.3)
  headers = { 'event' : 'click' }
  r = s.post(args.target + '?call=' + str(i),headers=headers)
  if(r.status_code==200):
    sys.stdout.write( str(i) + "-")
  else:
    sys.stdout.write( str(i) + "---->" + str(r.status_code) + "\n")
  sys.stdout.flush()
  i+=1
