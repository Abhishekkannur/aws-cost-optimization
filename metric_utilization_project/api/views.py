from django.http import JsonResponse
from .utils import get_all_ec2_instances, get_ec2_utilization,get_memory_utilization
from rest_framework.views import APIView
import boto3
from rest_framework import status
import csv
from rest_framework.response import Response
from django.http import HttpResponse
import os
import json
import argparse
import dateutil.relativedelta as dateutil
import datetime
import os
import sys
from django.shortcuts import HttpResponse
import boto3
import botocore.exceptions
from django.conf import settings
from datetime import datetime, timedelta , date
from django.shortcuts import render

AWS_ACCESS_KEY_ID = "AKIARTYY5VATZONBQLAO"
AWS_SECRET_ACCESS_KEY = "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"
AWS_S3_BUCKET_NAME = "project-employee-bucket"
AWS_REGION_NAME = "us-east-1"      # return Response({'download_link': download_link})
s3_client = boto3.client('s3',
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_REGION_NAME)
def generate_presigned_url(file_name):
    expiration = 3600  # Set the expiration time for 1 hour (you can adjust this as needed)
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET_NAME, "Key": file_name},
        ExpiresIn=expiration,
    )
    return url
class EC2_instances_list(APIView):
    def get(self,request):
            aws_access_key = "AKIARTYY5VATZONBQLAO"
            aws_secret_key = "5kyFiirpFU1gg6W2iAdoe9QTds/o46ePSMzkg1fM"
            region_name = 'us-east-1'  # Change to your desired AWS region
            instances_info=[]
            all_instances = get_all_ec2_instances(aws_access_key, aws_secret_key, region_name)
            for reservation in all_instances:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    state = instance['State']['Name']
                    
                    utilization_info = get_ec2_utilization(instance_id, aws_access_key, aws_secret_key, region_name)
                    if utilization_info:
                        instances_info.append({
                            'instance_id': instance_id,
                            'instance_type': instance_type,
                            'state': state,
                            'utilization_info': utilization_info
                })
                    
            return JsonResponse({'CPUUtilization_data': instances_info})

def get_ec2_data(request):
    return render(request,'ec2_memory_data.html')
class EC2_Memory_utilization(APIView):
     def get(self, request):
        all_utilization_info = []

        regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

        for region_name in regions:
            ec2_client = boto3.client('ec2', region_name=region_name)

            response = ec2_client.describe_instances()

            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    state = instance['State']['Name']

                    cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=30)

                    # Query for memory utilization
                    response = cloudwatch_client.get_metric_data(
                        MetricDataQueries=[
                            {
                                'Id': 'mem_utilization',
                                'MetricStat': {
                                    'Metric': {
                                        'Namespace': 'CWAgent',
                                        'MetricName': 'mem_used_percent',
                                        'Dimensions': [
                                            {
                                                'Name': 'InstanceId',
                                                'Value': instance_id
                                            },
                                        ]
                                    },
                                    'Period': 3600,
                                    'Stat': 'Average',
                                },
                                'ReturnData': True,
                            },
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                    )

                    # Query for CPU utilization
                    cpu_response = cloudwatch_client.get_metric_data(
                        MetricDataQueries=[
                            {
                                'Id': 'cpu_utilization',
                                'MetricStat': {
                                    'Metric': {
                                        'Namespace': 'AWS/EC2',
                                        'MetricName': 'CPUUtilization',
                                        'Dimensions': [
                                            {
                                                'Name': 'InstanceId',
                                                'Value': instance_id
                                            },
                                        ]
                                    },
                                    'Period': 3600,
                                    'Stat': 'Average',
                                },
                                'ReturnData': True,
                            },
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                    )

                    # Query for disk utilization
                    disk_response = cloudwatch_client.get_metric_data(
                        MetricDataQueries=[
                            {
                                'Id': 'disk_utilization',
                                'MetricStat': {
                                    'Metric': {
                                        'Namespace': 'CWAgent',
                                        'MetricName': 'disk_used_percent',
                                        'Dimensions': [
                                            {
                                                'Name': 'InstanceId',
                                                'Value': instance_id
                                            },
                                            {
                                                'Name': 'device',
                                                'Value': 'xvda1'
                                            },
                                            {
                                                'Name': 'fstype',
                                                'Value': 'ext4'
                                            },
                                            {
                                                'Name': 'path',
                                                'Value': '/'
                                            }
                                        ]
                                    },
                                    'Period': 3600,
                                    'Stat': 'Average',
                                },
                                'ReturnData': True,
                            },
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                    )

                    if 'MetricDataResults' in response:
                        for metric_result in response['MetricDataResults']:
                            if 'Values' in metric_result:
                                utilization_info = metric_result['Values']
                                if utilization_info:
                                    average_value = sum(utilization_info) / len(utilization_info)
                                    all_utilization_info.append({
                                        'instance_id': instance_id,
                                        'instance_type': instance_type,
                                        'state': state,
                                        'metric_type': 'memory',
                                        'average_utilization': average_value,
                                        'region': region_name,
                                    })

                    if 'MetricDataResults' in cpu_response:
                        for metric_result in cpu_response['MetricDataResults']:
                            if 'Values' in metric_result:
                                utilization_info = metric_result['Values']
                                if utilization_info:
                                    average_value = sum(utilization_info) / len(utilization_info)
                                    all_utilization_info.append({
                                        'instance_id': instance_id,
                                        'instance_type': instance_type,
                                        'state': state,
                                        'metric_type': 'cpu',
                                        'average_utilization': average_value,
                                        'region': region_name,
                                    })
                    
                    if 'MetricDataResults' in disk_response:
                        for metric_result in disk_response['MetricDataResults']:
                            if 'Values' in metric_result:
                                utilization_info = metric_result['Values']
                                if utilization_info:
                                    average_value = sum(utilization_info) / len(utilization_info)
                                    all_utilization_info.append({
                                        'instance_id': instance_id,
                                        'instance_type': instance_type,
                                        'state': state,
                                        'metric_type': 'disk',
                                        'average_utilization': average_value,
                                        'region': region_name,
                                    })

        response_json = json.dumps(all_utilization_info, indent=4)

        response = HttpResponse(response_json, content_type='application/json')

       
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"rds_instance_details_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

        return response
cloudwatch_client = boto3.client('cloudwatch')
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

def rds_data_view(request):
    return render(request, 'index.html')


class RDSData(APIView):
    def get(self,request):
        rds_client = boto3.client('rds')
        regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

        # Header for the CSV file
        header = "Region,DBInstanceIdentifier,Engine,DBInstanceClass,Status,InstanceType,DBConnectionsReadWrite,CPUUtilization,Storage"

        # Initialize data list with header
        data = [header]

        # Loop through each region
        for region in regions:
            #print(f"Fetching RDS details in {region}")

            # Initialize Boto3 client for RDS in the current region
            rds_client_region = boto3.client('rds', region_name=region)

            # Fetch RDS instances in the region
            instances = rds_client_region.describe_db_instances()['DBInstances']
            
            # Loop through each RDS instance and gather details
            for instance in instances:
                db_identifier = instance['DBInstanceIdentifier']
                engine = instance['Engine']
                db_instance_class = instance['DBInstanceClass']
                status = instance['DBInstanceStatus']
                instance_type = instance['DBInstanceClass']
                db_connections_read_write = instance.get('ReadReplicaSourceDBInstanceIdentifier', 'N/A')
                
                storage = instance.get('AllocatedStorage', 'N/A')
                # max_storage=instance.get('MaxAllocatedStorage')
                allocated_storage = instance['AllocatedStorage']
                

                # Get CloudWatch metrics for Storage and Free Storage
                namespace = 'AWS/RDS'
                metric_name = 'FreeStorageSpace'
                dimensions = [{'Name': 'DBInstanceIdentifier', 'Value': db_identifier}]
                cpu_response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_identifier}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 5-minute interval, adjust as needed
                    Statistics=['Average'],
                    Unit='Percent'
                )

                # Fetch FreeableMemory metric data from CloudWatch
                memory_response = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='FreeStorageSpace',
                    Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_identifier}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 5-minute interval, adjust as needed
                    Statistics=['Average'],
                    Unit='Bytes'
                )

                # Extract the average CPU and memory utilization from the responses
                avg_cpu_utilization = cpu_response['Datapoints'][-1]['Average'] if cpu_response.get('Datapoints') else None
                avg_memory_utilization = memory_response['Datapoints'][-1]['Average'] if memory_response.get('Datapoints') else None
                avg_memory_GiB = avg_memory_utilization / (1024 ** 3) if avg_memory_utilization else None
                user_memory=allocated_storage-avg_memory_GiB if avg_memory_GiB else None
                instance_data = {
                    'Region': region,
                    'DBInstanceIdentifier': db_identifier,
                    'Engine': engine,
                    'DBInstanceClass': db_instance_class,
                    'Status': status,
                    'InstanceType': instance_type,
                    'DBConnectionsReadWrite': db_connections_read_write,
                    'AllocatedStorage': allocated_storage,
                    'Storage': storage,
                    'CPUUtilization_in_percentage': avg_cpu_utilization,
                    'FreeStroargeSpace_in_GiB': avg_memory_GiB ,
                    'Used_Storage_in_GiB':user_memory ,
                }
                
                data.append(instance_data)

        response_data = {
            'RDSInstanceData': data,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        response_json = json.dumps(response_data, indent=4)

        # Set the response content type to JSON
        response = HttpResponse(response_json, content_type='application/json')

        # Set the 'Content-Disposition' header for download
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"rds_instance_details_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

        return response

def billing_data_view(request):
    return render(request, 'awsbilling.html')

class Get_Total_Bill(APIView):
    def get(self, request):
        billing_data = []
          # Rename the variable to avoid conflict
        client = boto3.client('ce', region_name='us-east-1')  # You can choose any region for the client
        # today = date.today()  # Use the renamed variable
        # first_day_of_month = today.replace(day=1)
        # last_day_of_month = today.replace(day=28) + timedelta(days=4)  # To handle months with varying lengths
        # start_date = first_day_of_month.strftime('%Y-%m-%d')
        # end_date = last_day_of_month.strftime('%Y-%m-%d')
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        metrics = ['BlendedCost']
        ec2_regions = boto3.Session().get_available_regions('ec2')
        for month in range(1, current_month + 1):
        # Get the first and last day of the current month
            first_day_of_month = datetime(current_year, month, 1)
            last_day_of_month = first_day_of_month.replace(day=28) + timedelta(days=4)  # To handle months with varying lengths

            # Format the dates in the required format for the API
            start_date = first_day_of_month.strftime('%Y-%m-%d')
            end_date = last_day_of_month.strftime('%Y-%m-%d')

            # Retrieve the cost and usage data for the current month
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=metrics
            )

            # Extract the cost for the current month
            cost = response['ResultsByTime'][0]['Total']['BlendedCost']['Amount']
            region_data = {
                'Month': f"{month:02d}/{current_year}",
                'TotalCost_in_USD': cost 
            }
            billing_data.append(region_data)
        response_data = {
            'AWS Billing': billing_data,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Use the renamed variable
        }
        response_json = json.dumps(response_data, indent=4)
        response = HttpResponse(response_json, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")  # Use the renamed variable
        dynamic_filename = f"AWS Billing_details_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
        return response

def get_secret_data(request):
    return render (request, 'secrets_data.html')
class Secrets_data(APIView):
    def get(self,request):
    
    # Get a list of all available AWS regions
        regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

        all_secrets = []

        for region in regions:
            

            # Create a Boto3 client for the AWS Secrets Manager service in the current region
            secrets_manager_client = boto3.client('secretsmanager', region_name=region)

            # List all secrets in the current region
            response = secrets_manager_client.list_secrets()

            secrets = response['SecretList']
            
            for secret in secrets:
                secret_name = secret['Name']
                secret_arn = secret['ARN']

                total_secrets = len(secrets)
                all_secrets.append({
                    'Region': region,
                    'Secret Name': secret_name,
                    'Secret ARN': secret_arn,
                    'Resource_count':total_secrets,
                })

        
        response_json = json.dumps(all_secrets, indent=4)
        response = HttpResponse(response_json, content_type='application/json')

        # Set the 'Content-Disposition' header for download
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"Secrets_details_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

        return response
def get_ecr_repositories(ecr_client):
    response = ecr_client.describe_repositories()
    return response['repositories']
def get_detail_ecr_data(request):
    return render (request,'ecr-data.html')
def get_repository_images(ecr_client, repository_name):
    response = ecr_client.describe_images(repositoryName=repository_name)
    return response['imageDetails']

def fetch_ecr_data_for_regions(request):
    ecr_data_list = []
    regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]
    for region in regions:
        ecr_client = boto3.client('ecr', region_name=region)
        repositories = get_ecr_repositories(ecr_client)
        
        for repository in repositories:
            repository_name = repository['repositoryName']
            images = get_repository_images(ecr_client, repository_name)
            ecr_data = {
                "Region": region,
                "Repository": repository_name,
                "Images": []
            }
            for image in images:
                image_pushedtime = image.get('imagePushedAt').isoformat() if image.get('imagePushedAt') else None
                image_lastpulltime = image.get('lastRecordedPullTime').isoformat() if image.get('lastRecordedPullTime') else None
                
                image_tags = image.get('imageTags', ['<no tags>'])
                image_size = image['imageSizeInBytes']
                image_size_mb = image_size / (1024 * 1024)
                ecr_data_image = {
                    
                    "Tags": image_tags,
                    "Size_in_mb": image_size_mb,
                    "lastpulltime": image_lastpulltime,
                    "pushedAtTime": image_pushedtime,
                }
                ecr_data["Images"].append(ecr_data_image)

            ecr_data_list.append(ecr_data)
    
    response_json = json.dumps(ecr_data_list, indent=4)
    response = HttpResponse(response_json, content_type='application/json')
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    dynamic_filename = f"ECR_details_{current_date}.json"
    response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

    return response

class Get_ECR_Data(APIView):
    def get(self, request):
        return fetch_ecr_data_for_regions(request)


def get_detail_s3_data(request):
    return render (request, 's3_data.html')

class Get_S3_Data(APIView):
    def get(self, request):
        s3_client = boto3.client('s3')

        three_days_ago = datetime.now() - timedelta(days=3)
        date = three_days_ago.strftime('%Y-%m-%d')

        # Get list of all S3 buckets
        response = s3_client.list_buckets()

        # Create a list to store bucket data
        bucket_data = []

        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            try:
                # Get bucket size and last modified date
                bucket_objects = s3_client.list_objects_v2(Bucket=bucket_name)
                total_size = 0
                last_modified = None
                object_count = 0
                storage_class = None

                if 'Contents' in bucket_objects:
                    object_count = len(bucket_objects['Contents'])
                    for obj in bucket_objects['Contents']:
                        storage_class = obj['StorageClass']
                        total_size += obj['Size']
                        if last_modified is None or obj['LastModified'] > last_modified:
                            last_modified = obj['LastModified']

                # Convert last modified date to a readable format without time
                formatted_last_modified = last_modified.strftime(
                    '%Y-%m-%d') if last_modified else 'N/A'
                
                # Check if the bucket's last modified date is earlier than the specified date
                if formatted_last_modified < date:
                    bucket_info = {
                        "Bucket": bucket_name,
                        "Total Storage Size (Bytes)": total_size,
                        "Last Modified Date": formatted_last_modified,
                        "Storage Class": storage_class,
                        "Object Count": object_count
                    }
                    bucket_data.append(bucket_info)
            except Exception as e:
                print("Error:", e)

        # Convert the bucket_data list to JSON format
        json_data = json.dumps(bucket_data, indent=4)

        response = HttpResponse(json_data, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"s3_details_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
        return response

        

  
def get_Lambda_Metrics(request):
    return render (request, 'lambda_data.html')
def fetch_lambda_metrics(lambda_function_name, region):
    try:
        cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'invocations',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/Lambda',
                            'MetricName': 'Invocations',
                            'Dimensions': [{'Name': 'FunctionName', 'Value': lambda_function_name}]
                        },
                        'Period': 3600,
                        'Stat': 'Sum'
                    }
                },
                {
                    'Id': 'duration',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/Lambda',
                            'MetricName': 'Duration',
                            'Dimensions': [{'Name': 'FunctionName', 'Value': lambda_function_name}]
                        },
                        'Period': 3600,
                        'Stat': 'Average'
                    }
                },
                {
                    'Id': 'concurrent_executions',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/Lambda',
                            'MetricName': 'ConcurrentExecutions',
                            'Dimensions': [{'Name': 'FunctionName', 'Value': lambda_function_name}]
                        },
                        'Period': 3600,
                        'Stat': 'Average'
                    }
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
        )

        invocations = response['MetricDataResults'][0]['Values']
        avg_duration = response['MetricDataResults'][1]['Values']
        concurrent_executions = response['MetricDataResults'][2]['Values']

        return invocations, avg_duration, concurrent_executions

    except Exception as e:
        print(f"An error occurred while fetching metrics for {lambda_function_name}: {e}")
        return None, None, None

class LambdaMetricsView(APIView):
    def get(self, request):
        try:
            lambda_client = boto3.client('lambda')
            functions = lambda_client.list_functions()

            metrics_data = []

            for function in functions['Functions']:
                function_name = function['FunctionName']
                region = function['FunctionArn'].split(':')[3]
                invocations, avg_duration, concurrent_executions = fetch_lambda_metrics(function_name, region)

                metrics_data.append({
                    "Function": function_name,
                    "Invocations": invocations,
                    "AvgDuration": avg_duration,
                    "ConcurrentExecutions": concurrent_executions
                })

            response_json = json.dumps(metrics_data, indent=4)
            response = HttpResponse(response_json, content_type='application/json')
            current_date = datetime.now().strftime("%Y-%m-%d")
            dynamic_filename = f"Lambda_details_{current_date}.json"
            response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
            return response
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {e}"}, status=500)

def get_detail_cost_data(request):
    return render (request, 'detail_aws_billing.html')
def get_month_year(date):
    return date.strftime('%b-%y')
class FetchAWSCostView(APIView):
    def get(self, request):
        try:
            client = boto3.client('ce', region_name='us-east-1')  # Using the Cost Explorer client

            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Fetch data for the last 3 months

            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',  # Monthly data
                Metrics=['UnblendedCost'],  # Cost data
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )

            cost_data = response['ResultsByTime']
            current_date = datetime.now().strftime("%Y-%m-%d")
            dynamic_filename = f"cost_details_{current_date}.csv"
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

            writer = csv.writer(response)
            writer.writerow(['Date', 'Service', 'Region', 'Amount', 'Unit'])

            total_cost = 0

            for entry in cost_data:
                date = entry['TimePeriod']['Start']
                groups = entry['Groups']

                for group in groups:
                    service = group['Keys'][0]
                    region = group['Keys'][1]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])

                    total_cost += cost

                    writer.writerow([get_month_year(datetime.strptime(date, '%Y-%m-%d')), service, region, cost, 'USD'])

            writer.writerow(['Total', '', '', total_cost, 'USD'])

            return response

        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")

def get_VPC_data(request):
    return render(request,'vpc_data.html')

class Get_VPCData(APIView):
    def get (self,request):
        
        aws_regions = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]
        ec2_clients = {region: boto3.client('ec2', region_name=region) for region in aws_regions}
        
        result = []  # List to store data for all regions

        for region, ec2_client_region in ec2_clients.items():
            region_data = {'Region': region, 'VPCs': []}

            vpcs_response = ec2_client_region.describe_vpcs()

            for vpc in vpcs_response['Vpcs']:
                vpc_id = vpc['VpcId']
                vpc_data = {'VPC ID': vpc_id, 'CIDR Block': vpc['CidrBlock'], 'Subnets': [], 'Internet Gateways': [], 'NAT Gateways': []}

                subnets_response = ec2_client_region.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

                for subnet in subnets_response['Subnets']:
                    subnet_data = {'Subnet ID': subnet['SubnetId'], 'Location': subnet['AvailabilityZone'], 'CIDR Block': subnet['CidrBlock']}
                    vpc_data['Subnets'].append(subnet_data)

                internet_gateways_response = ec2_client_region.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])

                for igw in internet_gateways_response['InternetGateways']:
                    vpc_data['Internet Gateways'].append({'IGW ID': igw['InternetGatewayId']})

                nat_gateways_response = ec2_client_region.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

                for nat_gw in nat_gateways_response['NatGateways']:
                    nat_gw_data = {'NAT Gateway ID': nat_gw['NatGatewayId'], 'Subnet': nat_gw['SubnetId'], 'Location': nat_gw['AvailabilityZone']}
                    vpc_data['NAT Gateways'].append(nat_gw_data)

                region_data['VPCs'].append(vpc_data)

            result.append(region_data)

        # Convert the result to JSON
        response_json = json.dumps(result, indent=4)

        # Create an HttpResponse with JSON content
        response = HttpResponse(response_json, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"VPC_data_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

        return response
    
def get_esc_data(request):
    return render(request,'ecs_data.html')
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(o)
class Get_ECS_Data(APIView):
    def get (self,request):
        cloudwatch_client = boto3.client('cloudwatch')

# Get a list of all AWS regions
        ec2_client = boto3.client('ec2', region_name='us-east-1')  # You can use any region to get the list of regions
        all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

        all_region_data = []  # List to store data for all regions

        # Loop through all AWS regions
        for region in all_regions:
            region_data = {'Region': region, 'Clusters': []}

            # Initialize ECS client for the current region
            ecs_client = boto3.client('ecs', region_name=region)

            # List all ECS clusters
            response = ecs_client.list_clusters()

            for cluster_arn in response['clusterArns']:
                cluster_name = cluster_arn.split('/')[-1]
                cluster_data = {'Cluster': cluster_name, 'Services': []}

                # List all services in the cluster
                services_response = ecs_client.list_services(cluster=cluster_name)

                for service_arn in services_response['serviceArns']:
                    service_name = service_arn.split('/')[-1]
                    service_data = {'Service': service_name, 'Metrics': []}

                    # Describe the service to get detailed information
                    service_details = ecs_client.describe_services(cluster=cluster_name, services=[service_name])

                    if 'services' in service_details and len(service_details['services']) > 0:
                        service = service_details['services'][0]
                        service_info = {
                            "Status": service['status'],
                            "Desired Count": service['desiredCount'],
                            "Running Count": service['runningCount'],
                            "Pending Count": service['pendingCount'],
                            "Task Definition": service['taskDefinition'],
                            "Created At": service['createdAt']
                        }

                        service_data['Service Info'] = service_info

                        metric_names = ["NetworkRxBytes", "NetworkTxBytes", "CpuUtilized", "MemoryUtilized"]
                        namespace = "ECS/ContainerInsights"
                        dimensions = [
                            {
                                "Name": "ClusterName",
                                "Value": cluster_name
                            },
                            {
                                "Name": "ServiceName",
                                "Value": service_name
                            }
                        ]

                        service_metrics = []

                        for metric_name in metric_names:
                            response = cloudwatch_client.get_metric_data(
                                MetricDataQueries=[
                                    {
                                        "Id": "ecs_metrics",
                                        "MetricStat": {
                                            "Metric": {
                                                "Namespace": namespace,
                                                "MetricName": metric_name,
                                                "Dimensions": dimensions
                                            },
                                            "Period": 3600,
                                            "Stat": "Average"
                                        },
                                    }
                                ],
                                StartTime="2022-04-28T00:00:00Z",
                                EndTime="2023-08-29T00:00:00Z",
                            )

                            values = response['MetricDataResults'][0].get('Values', [])
                            if values:
                                service_metrics.append({metric_name: values[0]})
                            else:
                                service_metrics.append({metric_name: "No data available"})

                        service_data['Metrics'] = service_metrics
                        cluster_data['Services'].append(service_data)

                region_data['Clusters'].append(cluster_data)

            all_region_data.append(region_data)

        # Convert the data to JSON format
        response_json = json.dumps(all_region_data, indent=4,cls=DateTimeEncoder)
        response = HttpResponse(response_json, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"VPC_data_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

        return response

def get_loadbalnacer_data(request):
    return render(request,'loadbalancer.html')
from statistics import mean
class Get_load_balancer_Data(APIView):
    def get(self,request):
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            cloudwatch_client = boto3.client('cloudwatch')
            namespace = 'AWS/ApplicationELB'
            response_period = 3600  # You can adjust the period as needed
            
            metrics = [
            {'Name': 'TargetResponseTime', 'Statistic': 'Average'},
            {'Name': 'ActiveConnectionCount', 'Statistic': 'Average'},
            {'Name': 'NewConnectionCount', 'Statistic': 'Sum'}
            ]
            # Metrics to retrieve

            # Get a list of available regions
            ec2_client = boto3.client('ec2')
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            result = []
            
            lb_metrics_list = []
# Iterate through each region
            for aws_region in regions:
                # Initialize the Elastic Load Balancing client for the region
                elbv2_client = boto3.client('elbv2', region_name=aws_region)

                # Describe load balancers to get their names and ARNs
                load_balancers = elbv2_client.describe_load_balancers()['LoadBalancers']

                # Iterate through each load balancer
                for lb in load_balancers:
                    load_balancer_arn = lb['LoadBalancerArn']
                    load_balancer_name = load_balancer_arn.split('loadbalancer/')[-1]
                    lb_metrics = []

                    # Iterate through each metric and retrieve statistics
                    for metric in metrics:
                        metric_name = metric['Name']
                        statistic = metric['Statistic']

                        # Get metric statistics data
                        response = cloudwatch_client.get_metric_statistics(
                            Namespace=namespace,
                            MetricName=metric_name,
                            Dimensions=[{'Name': 'LoadBalancer', 'Value': load_balancer_name}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,  # Adjust as needed
                            Statistics=[statistic],
                        )

                        # Extract values from response
                        data_points = response['Datapoints']

                        values = []
                        for point in data_points:
                            if statistic in point:
                                values.append(point[statistic])
                                

                        # Calculate average or sum
                        if statistic == 'Average':
                            metric_value = mean(values) if values else None
                        elif statistic == 'Sum':
                            metric_value = sum(values) if values else None
                        else:
                            metric_value = None
                        metric_data = {
                            'MetricName': metric_name,
                            'Statistic': statistic,
                            'MetricValue': metric_value,
                        }
                        lb_metrics.append(metric_data)

            # Add load balancer metrics to the result list
                    lb_metrics_list.append({
                        'Region': aws_region,
                        'LoadBalancerName': load_balancer_name,
                        'Metrics': lb_metrics,
                    })
                    
            response_json = json.dumps(lb_metrics_list, indent=4)
            response = HttpResponse(response_json, content_type='application/json')
            current_date = datetime.now().strftime("%Y-%m-%d")
            dynamic_filename = f"LoadBalancer_data_{current_date}.json"
            response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
            return response

def get_ebs_data(request):
    return render (request,'ebs_data.html')

class Get_EBS_Data(APIView):
    

        def get(self, request):
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            ec2_client = boto3.client('ec2')
            cloudwatch_client = boto3.client('cloudwatch')

            # Get a list of available regions
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

            # Initialize a list to store volume data across regions
            all_volume_data = []

            # Define the metric names for disk activity
            metric_names = ['VolumeReadOps', 'VolumeWriteOps']

            for aws_region in regions:
                ec2_client = boto3.client('ec2', region_name=aws_region)
                response = ec2_client.describe_volumes()

                # Iterate through each EBS volume
                for volume in response['Volumes']:
                    volume_id = volume['VolumeId']
                    volume_type = volume['VolumeType']
                    size_gb = volume['Size']
                    Iops = volume.get('Iops', None)  # Handle the case where 'Iops' may not be present

                    # Initialize a dictionary to store metrics for this volume
                    volume_metrics = {'VolumeId': volume_id, 'VolumeType': volume_type, 'SizeGB': size_gb, 'Iops': Iops}

                    # Retrieve and add I/O metrics for this volume
                    for metric_name in metric_names:
                        for stat in ['Average', 'Sum']:
                            metric_data = cloudwatch_client.get_metric_statistics(
                                Namespace='AWS/EBS',
                                MetricName=metric_name,
                                Dimensions=[{'Name': 'VolumeId', 'Value': volume_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=3600,  # Adjust as needed
                                Statistics=[stat],
                            )

                            # Extract and add the metric value to the volume_metrics dictionary
                            data_points = metric_data['Datapoints']
                            metric_value = None

                            if data_points:
                                metric_value = data_points[0][stat]

                            volume_metrics[f'{stat} {metric_name}'] = metric_value

                    # Get information about the EC2 instance associated with the volume
                    if 'Attachments' in volume:
                        attachments = volume['Attachments']
                        if attachments:
                            # Assuming a volume is attached to one instance (for simplicity)
                            instance_id = attachments[0]['InstanceId']
                            volume_metrics['InstanceId'] = instance_id

                    # Append the volume_metrics dictionary to the all_volume_data list
                    all_volume_data.append(volume_metrics)

            response_json = json.dumps(all_volume_data, indent=4)
            response = HttpResponse(response_json, content_type='application/json')
            current_date = datetime.now().strftime("%Y-%m-%d")
            dynamic_filename = f"EBS_data_{current_date}.json"
            response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
            return response
def get_waf_data(request):
    return render (request,'waf_data.html')
class Get_WAF_Data(APIView):
    def get (self,request):
        wafv2_client = boto3.client('wafv2')
        ec2_client = boto3.client('ec2')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

        # Initialize an empty list to store JSON objects
        json_response = []

        try:
            for aws_region in regions:
                cloudwatch_client = boto3.client('cloudwatch', region_name=aws_region)  # Initialize CloudWatch client per region
                response = wafv2_client.list_web_acls(Scope='CLOUDFRONT')
                
                for acl in response['WebACLs']:
                    acl_id = acl['Id']
                    name = acl['Name']

                    metric_name = 'AllowedRequests'
                    namespace = 'AWS/WAFV2'
                    rule_name = 'ALL'  # Specify 'ALL' to fetch data for all rules within the Web ACL
                    
                    dimensions = [
                        {
                            'Name': 'WebACL',
                            'Value': name,
                        },
                        {
                            'Name': 'Rule',
                            'Value': rule_name,
                        }
                    ]

                    end_time = datetime.utcnow()
                    start_time = end_time - timedelta(days=30)
                    
                    cloudwatch_response = cloudwatch_client.get_metric_data(
                        MetricDataQueries=[
                            {
                                'Id': 'm1',
                                'MetricStat': {
                                    'Metric': {
                                        'Namespace': namespace,
                                        'MetricName': metric_name,
                                        'Dimensions': dimensions,
                                    },
                                    'Period': 3600,
                                    'Stat': 'Average',
                                },
                            },
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        ScanBy='TimestampAscending',
                    )

                    if 'MetricDataResults' in cloudwatch_response:
                        for data_result in cloudwatch_response['MetricDataResults']:
                            if 'Values' in data_result:
                                values = data_result['Values']
                                
                                # Create a dictionary with the collected information
                                data_dict = {
                                    'AWS Region': aws_region,
                                    'Web ACL ID': acl_id,
                                    'Name': name,
                                    'Metric Name': metric_name,
                                    'Metric Values': values
                                }
                                
                                # Append the dictionary to the JSON response list
                                json_response.append(data_dict)
                    
        except Exception as e:
            return(f'Error: {str(e)}')

        # Serialize the JSON response list to a JSON string
        json_response_str = json.dumps(json_response, indent=4)
        response = HttpResponse(json_response_str, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"EBS_data_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
        return response

def get_volume_utilized_data(request):
    return render (request,'volume_data.html')
def run_df_command(instance_id, ssm_client):
    # Specify the command to run
    commands = ['df -hT && lsblk -o NAME,KNAME,SIZE,MOUNTPOINT,TYPE']

    # Send the command to the instance
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': commands},
    )

    # Wait for the command to complete
    command_id = response['Command']['CommandId']
    ssm_client.get_waiter('command_executed').wait(CommandId=command_id, InstanceId=instance_id)

    # Retrieve the command output
    output = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    return output
def parse_df_output(df_output):
    parsed_data = {}
    current_section = None

    for line in df_output:
        if line.startswith("Filesystem"):
            current_section = "Filesystem"
            parsed_data[current_section] = []
            parsed_data[current_section].append(line.strip())  # Add the header
        elif line.startswith("NAME"):
            current_section = "NAME"
            parsed_data[current_section] = []
            parsed_data[current_section].append(line.strip())  # Add the header
        elif current_section:
            if line.strip():
                parsed_data[current_section].append(line.strip())

    return parsed_data

class Get_Detailed_usage_Data(APIView):
    def get(self,request):
    # Initialize AWS clients
        ssm_client = boto3.client('ssm')
        ec2_client_global = boto3.client('ec2', region_name='us-east-1')  # You can choose any region to list all regions
        regions = [region['RegionName'] for region in ec2_client_global.describe_regions()['Regions']]

        response_data = []  # To store the response data

        for region_name in regions:
            ec2_client = boto3.client('ec2', region_name=region_name)

            # Describe all instances in the current region
            instances = ec2_client.describe_instances()

            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']

                    # Check if the instance is running
                    if instance['State']['Name'] == 'running':
                        output = run_df_command(instance_id, ssm_client)
                        
                        # Split the output into lines
                        lines = output['StandardOutputContent'].strip().split('\n')
                        
                        instance_info = {
                            "Region": region_name,
                            "InstanceID": instance_id,
                        }
                        
                        parsed_data = parse_df_output(lines)
                        instance_info.update(parsed_data)
                        
                        response_data.append(instance_info)

        json_response_str = json.dumps(response_data, indent=4)
        response = HttpResponse(json_response_str, content_type='application/json')
        current_date = datetime.now().strftime("%Y-%m-%d")
        dynamic_filename = f"EBS_data_{current_date}.json"
        response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'
        return response
    
                
    # def upload_to_s3(self, file_path, s3_bucket, s3_key):
    #     s3_client = boto3.client('s3')
    #     s3_client.upload_file(file_path, s3_bucket, s3_key)
    # def get(self, request):
    #     json_data = self.get_json_data()

    #     # Set the response content type to JSON
    #     response = JsonResponse({'RDSInstanceData': json_data}, json_dumps_params={'indent': 4})

    #     # Set the 'Content-Disposition' header for download
    #     current_date = datetime.now().strftime("%Y-%m-%d")
    #     dynamic_filename = f"rds_instance_details_{current_date}.json"
    #     response['Content-Disposition'] = f'attachment; filename="{dynamic_filename}"'

    #     return response
        

        # Save the CSV content to the file
        

        # s3_bucket = 'project-employee-bucket'
        # s3_key = 'rds_instance_details.csv'
        # self.upload_to_s3(file_path, s3_bucket, s3_key)
        # csv_url=generate_presigned_url(file_path)

        # Provide a link to the S3 object for download
        #s3_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_key}"
        #s3_url=csv_url
        # Delete the temporary file
        

        #return Response({'download_link': s3_url})
        # download_link = os.path.join(settings.MEDIA_URL, 'rds_instance_details.csv')
from io import BytesIO
import pandas as pd
import matplotlib

import matplotlib.pyplot as plt

class GetTotalBill(APIView):
     def get(self, request):
        try:
            client = boto3.client('ce', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )

            cost_data = response['ResultsByTime']

            data = []
            for entry in cost_data:
                date = entry['TimePeriod']['Start']
                groups = entry['Groups']
                for group in groups:
                    service = group['Keys'][0]
                    region = group['Keys'][1]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    data.append([date, service, region, cost])

            df = pd.DataFrame(data, columns=['Date', 'Service', 'Region', 'Cost'])

            # Prepare and return cost data as a list of dictionaries
            chart_data = []
            for date, service, cost in zip(df['Date'], df['Service'], df['Cost']):
                chart_data.append({'Date': date, 'Service': service, 'Cost': cost})

            return JsonResponse({'chart_data': chart_data})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def demo_billing_data_view(request):
    return render(request, 'demo_billing.html')


