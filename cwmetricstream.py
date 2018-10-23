#############################################################################
## cwmetricstream.py - A Lambda function that reads from a DynamoDB stream ##
## and pushes CloudWatch metrics to different event count namespaces.      ##
## Created by Luke Youngblood - lukey@amazon.com                           ##
## ----------------------------------------------------------------------- ##
## Set the following environment variables:                                ##
## REGION = the AWS region you would like to put CloudWatch metric data to ##
## AGENT_NAMESPACE = CloudWatch metric namespace for agent count events    ##
## EVENT_NAMESPACE = CloudWatch metric namespace for standard event counts ##
## REFERRAL_NAMESPACE = CloudWatch metric namespace for referral counts    ##
## PAGEVIEW_NAMESPACE = CloudWatch metric namespace for pageview counts    ##
## ANOMALY_NAMESPACE = CloudWatch metric namespace for anomaly scores      ##
############################################################################# 

import json
import boto3
from os import environ
from datetime import datetime
from collections import defaultdict

def put_cloudwatch_metric(event_name, event_datetime, event_count=1, cwc=boto3.client('cloudwatch', region_name=environ['REGION'])):
    event_name_list = event_name.split(':')
    if event_name_list[0] == 'agent_count':
        namespace=environ['AGENT_NAMESPACE']
        metricname=event_name_list[1]
    elif event_name_list[0] == 'event_count':
        namespace=environ['EVENT_NAMESPACE']
        metricname=event_name_list[1]
    elif event_name_list[0] == 'referral_count':
        namespace=environ['REFERRAL_NAMESPACE']
        metricname=event_name_list[1]
    elif event_name_list[0] == 'top_pages':
        namespace=environ['PAGEVIEW_NAMESPACE']
        metricname=event_name_list[1]
    elif event_name_list[0] == 'event_anomaly':
        namespace=environ['ANOMALY_NAMESPACE']
        metricname=event_name_list[1]
    elif event_name_list[0] == 'visitor_count':
        namespace=environ['EVENT_NAMESPACE'] # visitor_count goes in the standard event count namespace
        metricname=event_name_list[0] # This metric type simply has 'visitor_count' as the metric name
    metricData=[{
            'MetricName': metricname,
            'Timestamp': datetime.strptime(event_datetime, '%Y-%m-%dT%H:%M:%S'),
            'Value': event_count,
            'Unit': 'Count',
            'StorageResolution': 1
        },]
    response = cwc.put_metric_data(Namespace=namespace,MetricData=metricData)

def lambda_handler(event, context):
    events_int = defaultdict(int)
    events_float = defaultdict(float)
    for record in event['Records']:
        for metric in record['dynamodb']['NewImage']['MetricDetails']['L']:
            try: event_timestamp = metric['M']['EVENTTIMESTAMP']['N']
            except Exception as e:
                event_timestamp='NULL'

            if event_timestamp!='NULL':
                timestamp = float(event_timestamp) / 1000
                event_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S')

            metric_field = metric['M']['METRICTYPE']['S']
            if metric_field=='agent_count' or 'event_count' or 'referral_count' or 'top_pages':
                if metric['M']['METRICITEM']['S'] == 'null':
                    event_type = metric_field + ':No referrer' # split on : later
                else:
                    event_type = metric_field + ':' + metric['M']['METRICITEM']['S'] # split on : later
                event_value = metric['M']['UNITVALUEINT']['N'] # these metric types all have int values
                events_int[(event_type, event_time)] = int(event_value)
            elif metric_field == 'event_anomaly': # anomalies need to be split on :
                print "Anomaly detected!"
                event_type_list = metric['M']['METRICITEM']['S'].split(':')
                event_type = metric_field + ':' + event_type_list[0] # split on : later
                event_value = metric['M']['UNITVALUEFLOAT']['N'] # anomalies events have float values
                events_float[(event_type, event_time)] = float(event_value)
            elif metric_field == 'visitor_count':
                event_type = metric_field
                event_value = metric['M']['UNITVALUEINT']['N'] # visitor count events have int values
                events_int[(event_type, event_time)] = int(event_value)
            else: event_type = 'NULL'
      
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
        put_cloudwatch_metric(key[0], key[1], float(val))
    return 'Successfully processed {} records.'.format(len(event['Records']))