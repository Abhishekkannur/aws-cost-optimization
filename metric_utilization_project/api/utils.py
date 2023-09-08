import boto3
import datetime

def get_all_ec2_instances():
    try:
        ec2_client = boto3.client('ec2',)
        response = ec2_client.describe_instances()
        
        return response['Reservations']
    except Exception as e:
        print(f"Error: {e}")
        return []
def get_ec2_utilization(instance_id, aws_access_key, aws_secret_key, region_name):
    try:
        cloudwatch_client = boto3.client('cloudwatch', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=region_name)
        
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'cpu_utilization',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}]
                        },
                        'Period': 3600,  # 1 hour granularity
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=(datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
            EndTime=datetime.datetime.now().isoformat(),
            ScanBy='TimestampDescending'
        )
        
        if 'MetricDataResults' in response and len(response['MetricDataResults']) > 0:
            metric_data = response['MetricDataResults'][0]['Timestamps']
            cpu_utilization = response['MetricDataResults'][0]['Values']
            
            # Calculate average CPU utilization per day
            avg_cpu_utilization_per_day = {}
            for timestamp, value in zip(metric_data, cpu_utilization):
                date = timestamp.date()
                date_str = str(date)  # Convert date to string
                if date_str not in avg_cpu_utilization_per_day:
                    avg_cpu_utilization_per_day[date_str] = []
                avg_cpu_utilization_per_day[date_str].append(value)
            
            for date, values in avg_cpu_utilization_per_day.items():
                avg_utilization = sum(values) / len(values)
                avg_cpu_utilization_per_day[date] = avg_utilization
            
            return avg_cpu_utilization_per_day
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
def get_memory_utilization(instance_id, aws_access_key, aws_secret_key, region_name):
    try:
        # Initialize clients
        cloudwatch_client = boto3.client('cloudwatch', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=region_name)
#         ssm_client = boto3.client('ssm', region_name=region_name)

# # Specify the command to run
#         command = "free -m"

#         # Send the command
#         response = ssm_client.send_command(
#             InstanceIds=[instance_id],
#             DocumentName="AWS-RunShellScript",
#             Parameters={"commands": [command]},
#         )

#         command_id = response["Command"]["CommandId"]

#         # Wait for command execution to complete
#         ssm_client.get_waiter("command_executed").wait(
#             InstanceId=instance_id, CommandId=command_id
#         )

#         # Retrieve command output
#         command_output = ssm_client.get_command_invocation(
#             InstanceId=instance_id, CommandId=command_id
#         )

#         output = command_output["StandardOutputContent"]
        # Get memory utilization metrics
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'mem_used_percent',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'CWAgent',
                            'MetricName': 'mem_used_percent',
                            'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}]
                        },
                        'Period': 86400,  # 1 day granularity
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=(datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
            EndTime=datetime.datetime.now().isoformat(),
            ScanBy='TimestampDescending'
        )
        
        if 'MetricDataResults' in response and len(response['MetricDataResults']) > 0:
            
            results = response['MetricDataResults'][0]['Values']
            timestamps = response['MetricDataResults'][0]['Timestamps']
            
           
            daily_averages = {}
            for timestamp, value in zip(timestamps, results):
                timestamp = timestamp.timestamp()  # Convert to Unix timestamp
                date = datetime.datetime.fromtimestamp(timestamp).date()
                date_str = str(date)  # Convert date to string
                if date_str not in daily_averages:
                    daily_averages[date_str] = []
                daily_averages[date_str].append(value)
            
            
            for date, utilizations in daily_averages.items():
                daily_averages[date] = sum(utilizations) / len(utilizations)
                
            return {
                'InstanceId': instance_id,
                'AvgMemoryUtilizationPerDay': daily_averages,
                
            }
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None