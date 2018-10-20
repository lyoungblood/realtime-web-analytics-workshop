import json
import boto3
from os import environ
from datetime import datetime
from collections import defaultdict

def put_cloudwatch_metric(event_name, event_datetime, event_count=1, cwc=boto3.client('cloudwatch', region_name=environ['REGION'])):
    metricData=[{
            'MetricName': event_name,
            'Timestamp': datetime.strptime(event_datetime, '%Y-%m-%dT%H:%M:%S'),
            'Value': event_count,
            'Unit': 'Count',
            'StorageResolution': 1
        },]
    response = cwc.put_metric_data(Namespace=environ['NAMESPACE'],MetricData=metricData)

def lambda_handler(event, context):
    events_int = defaultdict(int)
    events_float = defaultdict(float)
    for record in event['Records']:
        for metric in record['dynamodb']['NewImage']['MetricDetails']['L']:
            try: event_type = metric['M']['METRICITEM']['S']
            except Exception as e:
                event_type='NULL'
            try: event_timestamp = metric['M']['EVENTTIMESTAMP']['N']
            except Exception as e:
                event_timestamp='NULL'
            if 'NULL' in metric['M']['UNITVALUEFLOAT']: # Is this an integer metric?
                try: event_value = metric['M']['UNITVALUEINT']['N']
                except Exception as e:
                    event_value='NULL'
            else: # Otherwise, it's a float metric.
                try: event_value = metric['M']['UNITVALUEFLOAT']['N']
                except Exception as e:
                    event_value='NULL'
                try: event_type_list = metric['M']['METRICITEM']['S'].split(':')
                except Exception as e:
                    event_type='NULL'
                if event_type!='NULL':
                    event_type=event_type_list[0]
            if event_timestamp!='NULL':
                timestamp = float(event_timestamp) / 1000
                event_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')
      
            if event_type!='NULL' and event_timestamp!='NULL':
                if 'NULL' in metric['M']['UNITVALUEFLOAT']:
                    events_int[(event_type, event_time)] = int(event_value)
                else:
                    events_float[(event_type, event_time)] = float(event_value)

    for key,val in events_int.iteritems():
        print "%s, %s = %d" % (key[0], key[1], val)
        put_cloudwatch_metric(key[0], key[1], int(val))
    for key,val in events_float.iteritems():
        print "%s, %s = %f" % (key[0], key[1], val)
        put_cloudwatch_metric(key[0], key[1], int(val))
    return 'Successfully processed {} records.'.format(len(event['Records']))