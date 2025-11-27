AWS RDS Automated Monitoring Framework

This framework automatically configures CloudWatch alarms for Amazon RDS whenever a database is created or deleted.
Alarms are based on CPU, Database Connections, and Freeable Memory, and thresholds are automatically adjusted based on the instance type capacity.

All logic is implemented inside:
📄 lambda_function/rds_event_alerting.py

The setup is triggered by:
📄 event_bridge/event_bridge_rule.json

Architecture reference:
📄 architecture_diagrams/monitoring-framework.drawio.png

📡 How It Works
1. Event Trigger

Whenever an RDS instance is created or deleted, the EventBridge rule detects events from:

eventSource = rds.amazonaws.com

eventName = CreateDBInstance, DeleteDBInstance

Only successful or non-DryRun events

This ensures the automation runs only when a real DB change takes place.

⚙️ Automatic Alarm Creation

For every new RDS instance, the Lambda function automatically creates two categories of alarms:

🔥 CRITICAL Alerts (High Severity)

Used for immediate action scenarios.

Configured using: 90% threshold/5 datapoints/5-minute evaluation period

Critical alarms include: High CPU Utilization/High Database Connections/Low Freeable Memory

Alerts are sent to: Slack/PagerDuty/Email

⚠️ WARNING Alerts (Medium Severity)

Used for early warning and investigation.

Configured using: 80% threshold/10 datapoints/10-minute evaluation period

Warning alarms include: CPU Utilization (above warning threshold)/Database Connections (above warning threshold)/Freeable Memory (below warning threshold)

Alerts go to:

General DB Email SNS Topic

🧠 How Thresholds Are Calculated Automatically

The Lambda function determines default thresholds based on RDS instance type capacity, using predefined mappings.

It uses two internal reference maps:

1. Instance Memory Map (Example Snippet)

The framework knows how much RAM each instance type has:

Instance Type	Memory
db.m5.large	    8 GB
db.r5.large	    16 GB


This is used to calculate FreeableMemory thresholds (critical & warning) dynamically.

2. Max Connection Map (Example Snippet)

The framework also knows the maximum DB connections per instance type:

Instance Type	Max Connections
db.m5.large	    683
db.r5.large	    1000
=

This is used to calculate: Critical connection threshold/Warning connection threshold

Automatically, based on % levels.


The framework reads this tag and sends both WARNING and CRITICAL alerts to the corresponding team SNS.

🗂 Alarm Lifecycle
CreateDBInstance

All WARNING and CRITICAL alarms are created

Thresholds depend on instance type

DeleteDBInstance

All alarms belonging to that DB instance are deleted automatically

🎉 Summary

This RDS monitoring framework provides:

Automatic creation of CPU, Connection, and Memory alarms

Dynamic threshold calculation based on instance type

Built-in WARNING and CRITICAL policies

Zero manual configuration

Fully EventBridge-driven automation