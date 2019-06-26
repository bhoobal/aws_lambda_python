#----------------------------------------------------------------------
#Check underutilzed instance
# Conditions to check 
#	if CPU utilization is <10 for 4 consequtive data points and
#	if NWpacket_in  < 50000 kb 
#		1. Stop theinstance
#----------------------------------------------------------------------
import json
import boto3
import logging
import datetime
import itertools

#setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

cw = boto3.client('cloudwatch')

#define the connection
ec2 = boto3.resource('ec2')

def lambda_handler(event, context):
    # TODO implement
    # Use the filter() method of the instances collection to retrieve
    # all running EC2 instances.
    #local variables
    n=0
    p=0
    cpu_util=0
    nw_in=0
    total=0
    stopList = []
    
    filters = [{
            'Name': 'tag:Name',
            'Values': ['CHN-*']
        },
        {
            'Name': 'instance-state-name', 
            'Values': ['running']
        },
        {
            'Name': 'tag:chn-low-utz-AutoStop',
            'Values': ['true']
        }
    ]
    #filter the instances
    instances = ec2.instances.filter(Filters=filters)

    #locate all running instances
    RunningInstances = [instance.id for instance in instances]
    
    for instance in instances:
        #print (instance.id)
        cpuutil=cw.get_metric_statistics(Period=900,StartTime=datetime.datetime.utcnow() - datetime.timedelta(seconds=3600),EndTime=datetime.datetime.utcnow(),MetricName='CPUUtilization',Namespace='AWS/EC2',Statistics=['Average'],Dimensions=[{'Name':'InstanceId', 'Value':str(instance.id)}])
        for k, v in cpuutil.items():
            if k == 'Datapoints':
               for y in v:
                   cpu_util=float("{0:.2f}".format(y['Average']))
                   if cpu_util < 10:
                       n=n+1
        if n >=4:
            #print ("Instance -->" instance.id  "is underutilized - Low CPU Utilization "]
            networkin=cw.get_metric_statistics(Period=900,StartTime=datetime.datetime.utcnow() - datetime.timedelta(seconds=3600),EndTime=datetime.datetime.utcnow(),MetricName='NetworkIn',Namespace='AWS/EC2',Statistics=['Average'],Dimensions=[{'Name':'InstanceId', 'Value':str(instance.id)}])
            for k, v in networkin.items():
                if k == 'Datapoints':
                    for y in v:
                        nw_in=float("{0:.2f}".format(y['Average']))
                        if nw_in < 50000:
                            p=p+1
                    if p >=4:
                        data=[instance.id,"Low","Low CPU & NW Utilization "]
                        print (data)
                        stopList.append(instance.id)
                        print (instance.id, " added to STOP list")
                        
    #make sure there are actually instances to shut down. 
    if len(RunningInstances) > 0:
        #perform the shutdown
        #  shuttingDown = ec2.instances.filter(InstanceIds=RunningInstances).stop()
        #ec2.stop_instances(InstanceIds=instances)
        print ("")
        #print ("shuttingDown")
    else:
        print ("There are no instances to validate")
    
    if stopList:
        print ("Stopping", len(stopList) ,"instances", stopList)
        ec2.instances.filter(InstanceIds=stopList).stop()
    else:
        print ("No Instances to Stop")
