import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from src.models import AwsCost, Metric, Resource, Department
import logging

logger = logging.getLogger(__name__)

class AWSService:
    def __init__(self):
        self._session = None
        self._ce_client = None
        self._cloudwatch_client = None
        self._resource_groups_client = None
    
    def is_configured(self) -> bool:
        return (AWS_ACCESS_KEY_ID is not None and 
                AWS_SECRET_ACCESS_KEY is not None and
                len(AWS_ACCESS_KEY_ID) > 0 and 
                len(AWS_SECRET_ACCESS_KEY) > 0)
    
    def _get_session(self):
        if self._session is None:
            if not self.is_configured():
                raise ValueError("AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
            self._session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        return self._session
    
    @property
    def ce_client(self):
        if self._ce_client is None:
            self._ce_client = self._get_session().client('ce')
        return self._ce_client
    
    @property
    def cloudwatch_client(self):
        if self._cloudwatch_client is None:
            self._cloudwatch_client = self._get_session().client('cloudwatch')
        return self._cloudwatch_client
    
    @property
    def resource_groups_client(self):
        if self._resource_groups_client is None:
            self._resource_groups_client = self._get_session().client('resource-groups')
        return self._resource_groups_client
    
    def test_connection(self) -> bool:
        if not self.is_configured():
            logger.warning("AWS credentials not configured")
            return False
        try:
            self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'End': datetime.now().strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            return True
        except Exception as e:
            logger.error(f"AWS connection test failed: {e}")
            return False
    
    def fetch_cost_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}
                ]
            )
            
            costs = []
            for result in response.get('ResultsByTime', []):
                period_start = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                period_end = datetime.strptime(result['TimePeriod']['End'], '%Y-%m-%d')
                
                for group in result.get('Groups', []):
                    service_name = group['Keys'][0] if group['Keys'] else 'Unknown'
                    resource_id = group['Keys'][1] if len(group['Keys']) > 1 else None
                    
                    blended_cost = float(group['Metrics']['BlendedCost']['Amount'])
                    usage_quantity = float(group['Metrics'].get('UsageQuantity', {}).get('Amount', 0))
                    usage_unit = group['Metrics'].get('UsageQuantity', {}).get('Unit', None)
                    
                    costs.append({
                        'service_name': service_name,
                        'resource_id': resource_id,
                        'cost': blended_cost,
                        'usage_quantity': usage_quantity,
                        'usage_unit': usage_unit,
                        'start_date': period_start,
                        'end_date': period_end
                    })
            
            return costs
        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            raise
    
    def fetch_cost_by_tags(self, start_date: datetime, end_date: datetime, tag_key: str = "Department") -> List[Dict[str, Any]]:
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'TAG', 'Key': tag_key}
                ]
            )
            
            department_costs = []
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    tag_value = group['Keys'][0].replace(f'{tag_key}$', '') if group['Keys'] else 'Untagged'
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    department_costs.append({
                        'tag_key': tag_key,
                        'tag_value': tag_value,
                        'cost': cost
                    })
            
            return department_costs
        except Exception as e:
            logger.error(f"Error fetching cost by tags: {e}")
            raise
    
    def fetch_cloudwatch_metrics(self, service_name: str, resource_id: str, 
                                  metric_names: List[str], start_time: datetime, 
                                  end_time: datetime, period: int = 3600) -> List[Dict[str, Any]]:
        metrics_data = []
        
        namespace_map = {
            'Amazon EC2': 'AWS/EC2',
            'Amazon RDS': 'AWS/RDS',
            'Amazon S3': 'AWS/S3',
            'AWS Lambda': 'AWS/Lambda',
            'Amazon DynamoDB': 'AWS/DynamoDB',
            'Amazon ElastiCache': 'AWS/ElastiCache',
            'Amazon ECS': 'AWS/ECS',
            'Amazon EKS': 'AWS/EKS',
            'Elastic Load Balancing': 'AWS/ELB',
            'Amazon CloudFront': 'AWS/CloudFront',
            'Amazon API Gateway': 'AWS/ApiGateway',
        }
        
        namespace = namespace_map.get(service_name, f'AWS/{service_name.replace("Amazon ", "").replace("AWS ", "")}')
        
        dimension_map = {
            'AWS/EC2': {'Name': 'InstanceId', 'Value': resource_id},
            'AWS/RDS': {'Name': 'DBInstanceIdentifier', 'Value': resource_id},
            'AWS/Lambda': {'Name': 'FunctionName', 'Value': resource_id},
            'AWS/DynamoDB': {'Name': 'TableName', 'Value': resource_id},
        }
        
        default_dimension = {'Name': 'ResourceId', 'Value': resource_id}
        dimension = dimension_map.get(namespace, default_dimension)
        
        for metric_name in metric_names:
            try:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=[dimension],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period,
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                for datapoint in response.get('Datapoints', []):
                    metrics_data.append({
                        'service_name': service_name,
                        'resource_id': resource_id,
                        'metric_name': metric_name,
                        'value': datapoint.get('Average', 0),
                        'unit': datapoint.get('Unit', ''),
                        'timestamp': datapoint['Timestamp'],
                        'dimensions': {
                            'max': datapoint.get('Maximum', 0),
                            'min': datapoint.get('Minimum', 0)
                        }
                    })
            except Exception as e:
                logger.warning(f"Error fetching metric {metric_name} for {resource_id}: {e}")
                continue
        
        return metrics_data
    
    def get_service_metrics_config(self, service_name: str) -> List[str]:
        metrics_config = {
            'Amazon EC2': ['CPUUtilization', 'NetworkIn', 'NetworkOut', 'DiskReadOps', 'DiskWriteOps'],
            'Amazon RDS': ['CPUUtilization', 'DatabaseConnections', 'FreeStorageSpace', 'ReadIOPS', 'WriteIOPS'],
            'AWS Lambda': ['Invocations', 'Duration', 'Errors', 'Throttles', 'ConcurrentExecutions'],
            'Amazon S3': ['BucketSizeBytes', 'NumberOfObjects'],
            'Amazon DynamoDB': ['ConsumedReadCapacityUnits', 'ConsumedWriteCapacityUnits', 'ThrottledRequests'],
            'Amazon ElastiCache': ['CPUUtilization', 'CacheHits', 'CacheMisses', 'CurrConnections'],
            'Elastic Load Balancing': ['RequestCount', 'HealthyHostCount', 'UnHealthyHostCount', 'Latency'],
            'Amazon CloudFront': ['Requests', 'BytesDownloaded', 'BytesUploaded', '4xxErrorRate', '5xxErrorRate'],
            'Amazon API Gateway': ['Count', 'Latency', '4XXError', '5XXError'],
        }
        return metrics_config.get(service_name, ['CPUUtilization'])
    
    def sync_cost_data(self, db: Session, days: int = 30) -> int:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        costs = self.fetch_cost_data(start_date, end_date)
        
        count = 0
        for cost_data in costs:
            existing = db.query(AwsCost).filter(
                AwsCost.service_name == cost_data['service_name'],
                AwsCost.resource_id == cost_data['resource_id'],
                AwsCost.start_date == cost_data['start_date'],
                AwsCost.end_date == cost_data['end_date']
            ).first()
            
            if existing:
                existing.cost = cost_data['cost']
                existing.usage_quantity = cost_data['usage_quantity']
                existing.usage_unit = cost_data['usage_unit']
            else:
                db_cost = AwsCost(
                    service_name=cost_data['service_name'],
                    resource_id=cost_data['resource_id'],
                    cost=cost_data['cost'],
                    usage_quantity=cost_data['usage_quantity'],
                    usage_unit=cost_data['usage_unit'],
                    start_date=cost_data['start_date'],
                    end_date=cost_data['end_date']
                )
                db.add(db_cost)
                count += 1
        
        db.commit()
        logger.info(f"Synced {count} new cost records")
        return count
    
    def sync_department_costs(self, db: Session, days: int = 30, tag_key: str = "Department") -> int:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        dept_costs = self.fetch_cost_by_tags(start_date, end_date, tag_key)
        
        count = 0
        for dept_data in dept_costs:
            dept = db.query(Department).filter(
                Department.tag_key == dept_data['tag_key'],
                Department.tag_value == dept_data['tag_value']
            ).first()
            
            if dept:
                dept.total_cost = dept_data['cost']
            else:
                dept = Department(
                    name=dept_data['tag_value'] or 'Untagged',
                    tag_key=dept_data['tag_key'],
                    tag_value=dept_data['tag_value'],
                    total_cost=dept_data['cost']
                )
                db.add(dept)
                count += 1
        
        db.commit()
        logger.info(f"Synced {count} new department records")
        return count
    
    def sync_metrics_for_resource(self, db: Session, service_name: str, 
                                   resource_id: str, days: int = 7) -> int:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        metric_names = self.get_service_metrics_config(service_name)
        metrics = self.fetch_cloudwatch_metrics(
            service_name, resource_id, metric_names, start_time, end_time
        )
        
        count = 0
        for metric_data in metrics:
            existing = db.query(Metric).filter(
                Metric.service_name == metric_data['service_name'],
                Metric.resource_id == metric_data['resource_id'],
                Metric.metric_name == metric_data['metric_name'],
                Metric.timestamp == metric_data['timestamp']
            ).first()
            
            if not existing:
                db_metric = Metric(
                    service_name=metric_data['service_name'],
                    resource_id=metric_data['resource_id'],
                    metric_name=metric_data['metric_name'],
                    value=metric_data['value'],
                    unit=metric_data['unit'],
                    timestamp=metric_data['timestamp'],
                    dimensions=metric_data['dimensions']
                )
                db.add(db_metric)
                count += 1
        
        db.commit()
        logger.info(f"Synced {count} new metric records for {resource_id}")
        return count

aws_service = AWSService()
