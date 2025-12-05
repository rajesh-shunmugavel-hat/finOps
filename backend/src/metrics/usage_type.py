import boto3
from datetime import datetime, timedelta
import csv
import sys

PROFILE_NAME = "finops"  # <-- Change your AWS profile name here

def get_last_6_months_service_usage_type_cost():
    session = boto3.Session(profile_name=PROFILE_NAME)
    client = session.client('ce', region_name='us-east-1')

    end_date = datetime.utcnow().date().replace(day=1)
    start_date = (end_date - timedelta(days=180)).replace(day=1)

    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "DIMENSION", "Key": "USAGE_TYPE"}
        ]
    )

    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "service", "usagetype", "cost"])

    for result in response['ResultsByTime']:
        month = result['TimePeriod']['Start']
        for group in result['Groups']:
            service = group['Keys'][0]
            usage_type = group['Keys'][1]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])

            if amount > 0:
                writer.writerow([month, service, usage_type, f"{amount:.4f}"])

def get_last_6_months_service_api_operation_cost():
    session = boto3.Session(profile_name=PROFILE_NAME)
    client = session.client('ce', region_name='us-east-1')

    end_date = datetime.utcnow().date().replace(day=1)
    start_date = (end_date - timedelta(days=180)).replace(day=1)

    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "DIMENSION", "Key": "OPERATION"}
        ]
    )

    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "service", "api_operation", "cost"])

    for result in response['ResultsByTime']:
        month = result['TimePeriod']['Start']
        for group in result['Groups']:
            service = group['Keys'][0]
            usage_type = group['Keys'][1]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])

            if amount > 0:
                writer.writerow([month, service, usage_type, f"{amount:.4f}"])

def get_last_6_months_service_tag_based_cost():
    session = boto3.Session(profile_name=PROFILE_NAME)
    client = session.client('ce', region_name='us-east-1')
    TAG_KEYS = ["Project", "Owner", "Name"]  # tags to fetch

    end_date = datetime.utcnow().date().replace(day=1)
    start_date = (end_date - timedelta(days=180)).replace(day=1)

    writer = csv.writer(sys.stdout)
    writer.writerow(["date", "service", "tag_key", "tag_value", "cost"])

    for tag in TAG_KEYS:
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {"Type": "DIMENSION", "Key": "SERVICE"},
                {"Type": "TAG", "Key": tag}
            ]
        )

        for result in response['ResultsByTime']:
            month = result['TimePeriod']['Start']
            for group in result['Groups']:
                service = group['Keys'][0] or "UnknownService"
                raw_value = group['Keys'][1] or "None"
                tag_value = raw_value.split("$")[-1]  # removes Owner$, Project$, Name$ prefixes
                amount = float(group['Metrics']['UnblendedCost']['Amount'])

                if amount > 0:
                    writer.writerow([
                        month,
                        service,
                        tag,
                        tag_value,
                        f"{amount:.4f}"
                    ])


if __name__ == "__main__":
    #get_last_6_months_service_usage_type_cost()
    #get_last_6_months_service_api_operation_cost()
    get_last_6_months_service_tag_based_cost()
