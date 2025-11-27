import boto3
from datetime import datetime, timedelta
import json

# Environment Variables
RegionName = 'ap-south-1'

# SNS Topic ARNs
slack_sns_arn = "replace_your_aacount_arn:slack_sns_arn"
pagerduty_sns_arn = "replace_your_aacount_arn:pagerduty_sns_arn"
prod_db_alerts_sns_arn = "replace_your_aacount_arn:email_sns_arn"

# DB Instance Type to Memory Size Mapping (in bytes)
db_instance_memory = {
    'db.m5.large': 8 * 1024 * 1024 * 1024,   # 8 GB
    'db.m6g.large': 8 * 1024 * 1024 * 1024,   # 8 GB
    'db.r5.2xlarge': 64 * 1024 * 1024 * 1024, # 64 GB
    'db.r5.large': 16 * 1024 * 1024 * 1024,   # 16 GB
    'db.r5.4xlarge': 128 * 1024 * 1024 * 1024, # 128 GB
    'db.r5.xlarge': 32 * 1024 * 1024 * 1024,   # 32 GB
    'db.t3.small': 2 * 1024 * 1024 * 1024,    # 2 GB
    'db.r6g.xlarge': 32 * 1024 * 1024 * 1024,  # 32 GB
    'db.r6g.large': 16 * 1024 * 1024 * 1024,   # 16 GB
    'db.t3.micro': 1 * 1024 * 1024 * 1024,     # 1 GB
    'db.m6g.large': 8 * 1024 * 1024 * 1024,    # 8 GB
    'db.r5.8xlarge': 256 * 1024 * 1024 * 1024,  # 256 GB
    'db.m5.xlarge': 16 * 1024 * 1024 * 1024,   # 16 GB
    'db.m5.2xlarge': 32 * 1024 * 1024 * 1024,   # 32 GB
    'db.m5.4xlarge': 64 * 1024 * 1024 * 1024,   # 64 GB
    'db.m5.12xlarge': 192 * 1024 * 1024 * 1024, # 192 GB
    'db.t3.medium': 4 * 1024 * 1024 * 1024,     # 4 GB
    'db.t3.large': 8 * 1024 * 1024 * 1024,      # 8 GB
    'db.r6g.2xlarge': 64 * 1024 * 1024 * 1024,  # 64 GB
    'db.r6g.4xlarge': 128 * 1024 * 1024 * 1024, # 128 GB
    'db.r6g.12xlarge': 384 * 1024 * 1024 * 1024, # 384 GB
    'db.r6g.16xlarge': 512 * 1024 * 1024 * 1024, # 512 GB
    'db.t2.micro': 1 * 1024 * 1024 * 1024,      # 1 GB
    'db.t2.small': 2 * 1024 * 1024 * 1024,      # 2 GB
    'db.t2.medium': 4 * 1024 * 1024 * 1024,     # 4 GB
    'db.r7g.large': 64 * 1024 * 1024 * 1024,    # 64 GB
}

# Max connections mapping
db_instance_connections = {
    'db.m5.large': 683,
    'db.m6g.large': 683,
    'db.r5.2xlarge': 3000,
    'db.r5.large': 1000,
    'db.r5.4xlarge': 4000,
    'db.r5.xlarge': 2000,
    'db.t3.small': 45,
    'db.r6g.xlarge': 2000,
    'db.r6g.large': 1000,
    'db.t3.micro': 85,
    'db.m6g.large': 683,
    'db.r5.8xlarge': 5000,
    'db.m5.xlarge': 1365,
    'db.m5.2xlarge': 2731,
    'db.m5.4xlarge': 5461,
    'db.m5.12xlarge': 16384,
    'db.t3.medium': 90,
    'db.t3.large': 135,
    'db.r6g.2xlarge': 3000,
    'db.r6g.4xlarge': 4000,
    'db.r6g.12xlarge': 6000,
    'db.r6g.16xlarge': 6000,
    'db.t2.micro': 85,
    'db.t2.small': 45,
    'db.t2.medium': 90,
    'db.r7g.large': 1000,
}

def get_db_instance_type(db_instance_id):
    client_rds = boto3.client('rds', region_name=RegionName)
    try:
        response = client_rds.describe_db_instances(DBInstanceIdentifier=db_instance_id)
        db_instance = response['DBInstances'][0]
        instance_type = db_instance['DBInstanceClass']
        return instance_type
    except Exception as e:
        print(f"Error fetching DB instance details: {e}")
        return 'db.t3.micro'  # Default type if there's an error

def create_rds_cloudwatch_alarms(db_instance_id):
    db_instance_type = get_db_instance_type(db_instance_id)
    client_cw = boto3.client('cloudwatch', region_name=RegionName)
    
    memory_size = db_instance_memory.get(db_instance_type, 8 * 1024 * 1024 * 1024)
    warning_memory_threshold = 0.20 * memory_size
    critical_memory_threshold = 0.10 * memory_size
    
    max_connections = db_instance_connections.get(db_instance_type, 100)
    warning_connection_threshold = 0.80 * max_connections
    critical_connection_threshold = 0.90 * max_connections
    
    alarms = [
        {
            'AlarmName': f"[CRITICAL]{db_instance_id}-High-CPU-Utilization",
            'MetricName': 'CPUUtilization',
            'ComparisonOperator': 'GreaterThanThreshold',
            'Threshold': 90,
            'EvaluationPeriods': 5,
            'Actions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn],
            'OKActions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn]
        },
        {
            'AlarmName': f"[CRITICAL]{db_instance_id}-High-Database-Connections",
            'MetricName': 'DatabaseConnections',
            'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
            'Threshold': critical_connection_threshold,
            'EvaluationPeriods': 5,
            'Actions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn],
            'OKActions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn]
        },
        {
            'AlarmName': f"[CRITICAL]{db_instance_id}-Low-Freeable-Memory",
            'MetricName': 'FreeableMemory',
            'ComparisonOperator': 'LessThanThreshold',
            'Threshold': critical_memory_threshold,
            'EvaluationPeriods': 5,
            'Actions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn],
            'OKActions': [slack_sns_arn, pagerduty_sns_arn, prod_db_alerts_sns_arn]
        },
        {
            'AlarmName': f"[WARNING]{db_instance_id}-High-CPU-Utilization",
            'MetricName': 'CPUUtilization',
            'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
            'Threshold': 80,
            'EvaluationPeriods': 10,
            'Actions': [prod_db_alerts_sns_arn],
            'OKActions': [prod_db_alerts_sns_arn]
        },
        {
            'AlarmName': f"[WARNING]{db_instance_id}-High-Database-Connections",
            'MetricName': 'DatabaseConnections',
            'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
            'Threshold': warning_connection_threshold,
            'EvaluationPeriods': 10,
            'Actions': [prod_db_alerts_sns_arn],
            'OKActions': [prod_db_alerts_sns_arn]
        },
        {
            'AlarmName': f"[WARNING]{db_instance_id}-Low-Freeable-Memory",
            'MetricName': 'FreeableMemory',
            'ComparisonOperator': 'LessThanThreshold',
            'Threshold': warning_memory_threshold,
            'EvaluationPeriods': 10,
            'Actions': [prod_db_alerts_sns_arn],
            'OKActions': [prod_db_alerts_sns_arn]
        }
    ]
    
    for alarm in alarms:
        client_cw.put_metric_alarm(
            AlarmName=alarm['AlarmName'],
            ComparisonOperator=alarm['ComparisonOperator'],
            EvaluationPeriods=alarm['EvaluationPeriods'],
            MetricName=alarm['MetricName'],
            Namespace='AWS/RDS',
            Period=60,
            Threshold=alarm['Threshold'],
            ActionsEnabled=True,
            AlarmActions=alarm['Actions'],
            OKActions=alarm.get('OKActions', []),
            Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}],
            Statistic='Average'
        )

def delete_rds_cloudwatch_alarms(db_instance_id):
    client_cw = boto3.client('cloudwatch', region_name=RegionName)
    paginator = client_cw.get_paginator('describe_alarms')

    alarm_names = []

    for page in paginator.paginate():
        for alarm in page['MetricAlarms']:
            # Check if the alarm is associated with the given DBInstanceIdentifier
            for dimension in alarm['Dimensions']:
                if dimension['Name'] == 'DBInstanceIdentifier' and dimension['Value'] == db_instance_id:
                    alarm_names.append(alarm['AlarmName'])
    
    if alarm_names:
        client_cw.delete_alarms(AlarmNames=alarm_names)
        print(f"Deleted CloudWatch alarm: {alarm_names} for DB instance: {db_instance_id}")


def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    try:
        # Check if this is an RDS event from CloudTrail
        if 'detail' in event and 'eventSource' in event['detail'] and event['detail']['eventSource'] == 'rds.amazonaws.com':
            event_name = event['detail'].get('eventName')
            
            # Extract DB instance identifier from requestParameters
            if 'requestParameters' in event['detail'] and 'dBInstanceIdentifier' in event['detail']['requestParameters']:
                db_instance_id = event['detail']['requestParameters']['dBInstanceIdentifier']
                print(f"Processing event {event_name} for DB instance: {db_instance_id}")

                # Handle instance creation
                if event_name == 'CreateDBInstance':
                    print(f"Creating CloudWatch alarms for DB instance: {db_instance_id}")
                    create_rds_cloudwatch_alarms(db_instance_id)
                
                # Handle instance deletion
                elif event_name == 'DeleteDBInstance':
                    print(f"Deleting CloudWatch alarms for DB instance: {db_instance_id}")
                    delete_rds_cloudwatch_alarms(db_instance_id)
            else:
                print("No DB instance identifier found in the event")
        else:
            print("Event is not a relevant RDS CloudTrail event")

    except Exception as e:
        print(f"Error processing event: {str(e)}")
        raise

    return {
        'statusCode': 200,
        'body': json.dumps("Processed RDS instance event successfully")
    }