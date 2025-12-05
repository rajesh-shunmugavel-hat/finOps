"""
AWS Cost Explorer + CloudWatch Metric Discovery with Schema-Based Storage
Creates schema 'cloudwatch_metrics' with tables: {service_name}_{metric_name}
"""

import boto3
import sqlite3
from datetime import datetime, timedelta
import json
import re

class AWSCostMetricDiscovery:
    def __init__(self, profile_name='finops', region='us-east-1', top_n_metrics=10, db_name='aws_metrics.db'):
        # Initialize session with given profile name
        self.session = boto3.Session(profile_name=profile_name)

        self.ce_client = self.session.client('ce', region_name=region)
        self.cw_client = self.session.client('cloudwatch', region_name=region)

        self.profile_name = profile_name
        self.region = region
        self.top_n_metrics = top_n_metrics
        self.db_name = db_name

        self.conn = None
        self.schema_name = 'cloudwatch_metrics'

        
        # Mapping from Cost Explorer service names to CloudWatch namespaces
        self.service_to_namespace = {
            'Amazon Elastic Compute Cloud - Compute': 'AWS/EC2',
            'EC2 - Other': 'AWS/EC2',
            'Amazon Virtual Private Cloud': 'AWS/EC2',
            'Amazon Simple Storage Service': 'AWS/S3',
            'Amazon Relational Database Service': 'AWS/RDS',
            'AWS Lambda': 'AWS/Lambda',
            'Amazon DynamoDB': 'AWS/DynamoDB',
            'Amazon Elastic Load Balancing': 'AWS/ELB',
            'Application Load Balancer': 'AWS/ApplicationELB',
            'Network Load Balancer': 'AWS/NetworkELB',
            'Amazon CloudFront': 'AWS/CloudFront',
            'Amazon API Gateway': 'AWS/ApiGateway',
            'Amazon ElastiCache': 'AWS/ElastiCache',
            'Amazon Elasticsearch Service': 'AWS/ES',
            'Amazon Kinesis': 'AWS/Kinesis',
            'Amazon SNS': 'AWS/SNS',
            'Amazon SQS': 'AWS/SQS',
            'Amazon ECS': 'AWS/ECS',
            'Amazon EKS': 'AWS/EKS',
            'Amazon Redshift': 'AWS/Redshift',
            'Amazon CloudWatch': 'AWS/CloudWatch',
            'Amazon Route 53': 'AWS/Route53',
            'AWS Step Functions': 'AWS/States',
            'Amazon Aurora': 'AWS/RDS',
            'Amazon DocumentDB': 'AWS/DocDB',
            'Amazon Neptune': 'AWS/Neptune',
            'AWS Glue': 'AWS/Glue',
            'Amazon EMR': 'AWS/EMR',
            'Amazon MSK': 'AWS/Kafka',
            'AWS Backup': 'AWS/Backup',
            'Amazon FSx': 'AWS/FSx',
            'Amazon EFS': 'AWS/EFS',
            'AWS Transfer Family': 'AWS/Transfer',
            'Amazon WorkSpaces': 'AWS/WorkSpaces',
            'Amazon Cognito': 'AWS/Cognito',
            'Amazon Simple Email Service': 'AWS/SES',
            'AWS Secrets Manager': 'AWS/SecretsManager',
        }
        
        # Business-relevant metric patterns
        self.priority_patterns = [
            r'(?i)(cpu|memory|disk|storage).*util',
            r'(?i)utilization',
            r'(?i)(active|concurrent).*connection',
            r'(?i)(request|invocation|message|event).*count',
            r'(?i)(read|write|get|put|post).*count',
            r'(?i)throughput',
            r'(?i)processed.*bytes',
            r'(?i)(duration|latency|time)',
            r'(?i)response.*time',
            r'(?i)(error|fault|throttle).*count',
            r'(?i)4xx|5xx',
            r'(?i)failed.*count',
            r'(?i)unhealthy.*host',
            r'(?i)capacity.*unit',
            r'(?i)database.*connection',
            r'(?i)queue.*depth',
        ]
        
        self.exclude_patterns = [
            r'(?i)billing',
            r'(?i)quota',
            r'(?i)estimated.*charge',
            r'(?i)free.*tier',
        ]
    
    def init_database(self):
        """Initialize SQLite database with cloudwatch_metrics schema"""
        print(f"\n🗄️  Initializing database: {self.db_name}")
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()
        
        # Note: SQLite doesn't support schemas like PostgreSQL
        # We'll use naming convention: cloudwatch_metrics_{service}_{metric}
        # Create a catalog table to track all metric tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloudwatch_metrics_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT UNIQUE NOT NULL,
                service_name TEXT NOT NULL,
                namespace TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                dimensions TEXT,
                service_cost REAL,
                relevance_score INTEGER,
                record_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print(f"✅ Schema '{self.schema_name}' initialized with catalog table")
    
    def sanitize_name(self, text):
        """Sanitize service/metric name for table naming"""
        # Remove special characters, replace spaces/dashes with underscore
        clean = re.sub(r'[^a-zA-Z0-9]', '_', text)
        # Remove consecutive underscores
        clean = re.sub(r'_+', '_', clean)
        # Remove leading/trailing underscores
        clean = clean.strip('_')
        # Convert to lowercase
        return clean.lower()
    
    def create_table_name(self, service_name, metric_name):
        """Create table name: cloudwatch_metrics_{service}_{metric}"""
        service_clean = self.sanitize_name(service_name)
        metric_clean = self.sanitize_name(metric_name)
        
        # Truncate if too long (SQLite has 64 char limit for identifiers)
        table_name = f"{self.schema_name}_{service_clean}_{metric_clean}"
        
        if len(table_name) > 63:
            # Truncate metric name if needed
            available = 63 - len(f"{self.schema_name}_{service_clean}_")
            metric_clean = metric_clean[:available]
            table_name = f"{self.schema_name}_{service_clean}_{metric_clean}"
        
        return table_name
    
    def create_metric_table(self, table_name):
        """Create individual metric table"""
        cursor = self.conn.cursor()
        
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                average REAL,
                sum REAL,
                minimum REAL,
                maximum REAL,
                sample_count REAL,
                unit TEXT,
                dimensions TEXT,
                UNIQUE(timestamp, dimensions)
            )
        ''')
        
        # Create index on timestamp for time-series queries
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp 
            ON {table_name}(timestamp)
        ''')
        
        self.conn.commit()
    
    def get_services_with_costs(self, months=6):
        """Query Cost Explorer for services with non-zero costs"""
        print(f"\n🔍 Querying AWS Cost Explorer for last {months} months...")
        
        end_date = datetime.now().date()
        start_date = (end_date - timedelta(days=30 * months))
        
        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        services_with_cost = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if cost > 0:
                    if service_name not in services_with_cost:
                        services_with_cost[service_name] = 0
                    services_with_cost[service_name] += cost
        
        sorted_services = sorted(
            services_with_cost.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        print(f"✅ Found {len(sorted_services)} services with costs > $0.00")
        for service, cost in sorted_services:
            print(f"   💰 {service}: ${cost:.2f}")
        
        return dict(sorted_services)
    
    def map_services_to_namespaces(self, services):
        """Map Cost Explorer services to CloudWatch namespaces"""
        print("\n🗺️  Mapping services to CloudWatch namespaces...")
        
        mapped = {}
        unmapped = []
        
        for service in services.keys():
            namespace = self.service_to_namespace.get(service)
            if namespace:
                mapped[service] = namespace
                print(f"   ✓ {service} → {namespace}")
            else:
                unmapped.append(service)
        
        if unmapped:
            print(f"\n⚠️  {len(unmapped)} services without namespace mapping:")
            for s in unmapped:
                print(f"   ⚠️  {s}")
        
        return mapped
    
    def discover_metrics(self, namespace):
        """Discover all available metrics for a namespace"""
        print(f"\n📊 Discovering metrics for {namespace}...")
        
        metrics = []
        paginator = self.cw_client.get_paginator('list_metrics')
        
        try:
            for page in paginator.paginate(Namespace=namespace):
                metrics.extend(page['Metrics'])
        except Exception as e:
            print(f"   ❌ Error discovering metrics: {str(e)}")
            return []
        
        print(f"   ✅ Found {len(metrics)} total metrics")
        return metrics
    
    def calculate_metric_score(self, metric_name):
        """Score metric based on business relevance"""
        score = 0
        
        for pattern in self.priority_patterns:
            if re.search(pattern, metric_name):
                score += 10
        
        for pattern in self.exclude_patterns:
            if re.search(pattern, metric_name):
                score -= 100
        
        high_value_terms = ['request', 'error', 'cpu', 'latency', 'throughput']
        for term in high_value_terms:
            if term.lower() in metric_name.lower():
                score += 5
        
        return score
    
    def filter_and_rank_metrics(self, metrics):
        """Filter and rank metrics by business relevance"""
        scored_metrics = []
        
        for metric in metrics:
            metric_name = metric['MetricName']
            score = self.calculate_metric_score(metric_name)
            
            if score > 0:
                scored_metrics.append({
                    'metric': metric,
                    'score': score,
                    'name': metric_name
                })
        
        scored_metrics.sort(key=lambda x: x['score'], reverse=True)
        return scored_metrics[:self.top_n_metrics]
    
    def fetch_metric_statistics(self, namespace, metric_name, dimensions, days=30):
        """Fetch 1 month of metric statistics from CloudWatch"""
        print(f"   📈 Fetching {days} days of data for {metric_name}...")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        try:
            response = self.cw_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour intervals
                Statistics=['Average', 'Sum', 'Minimum', 'Maximum', 'SampleCount']
            )
            
            datapoints = response.get('Datapoints', [])
            print(f"      ✓ Retrieved {len(datapoints)} datapoints")
            return datapoints
            
        except Exception as e:
            print(f"      ❌ Error fetching statistics: {str(e)}")
            return []
    
    def store_metric_data(self, table_name, datapoints, dimensions, unit='None'):
        """Store metric datapoints in specific table"""
        if not datapoints:
            return 0
        
        cursor = self.conn.cursor()
        dim_str = json.dumps(dimensions) if dimensions else None
        stored = 0
        
        for dp in datapoints:
            try:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name}
                    (timestamp, average, sum, minimum, maximum, sample_count, unit, dimensions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    dp['Timestamp'],
                    dp.get('Average'),
                    dp.get('Sum'),
                    dp.get('Minimum'),
                    dp.get('Maximum'),
                    dp.get('SampleCount'),
                    unit,
                    dim_str
                ))
                stored += 1
            except Exception as e:
                print(f"      ⚠️  Error storing datapoint: {str(e)}")
        
        self.conn.commit()
        print(f"      ✓ Stored {stored} datapoints in {table_name}")
        return stored
    
    def register_in_catalog(self, table_name, service_name, namespace, metric_name, 
                           dimensions, cost, score, record_count):
        """Register metric table in catalog"""
        cursor = self.conn.cursor()
        dim_str = json.dumps(dimensions) if dimensions else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO cloudwatch_metrics_catalog
            (table_name, service_name, namespace, metric_name, dimensions, 
             service_cost, relevance_score, record_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (table_name, service_name, namespace, metric_name, dim_str, 
              cost, score, record_count))
        
        self.conn.commit()
    
    def run(self):
        """Main execution flow with schema-based table storage"""
        print("=" * 70)
        print("AWS COST + CLOUDWATCH DISCOVERY - SCHEMA-BASED STORAGE")
        print(f"Schema: {self.schema_name}")
        print(f"Table Format: {self.schema_name}_{{service}}_{{metric}}")
        print("=" * 70)
        
        # Initialize database
        self.init_database()
        
        # Step 1: Get services with costs
        services_with_cost = self.get_services_with_costs()
        
        if not services_with_cost:
            print("❌ No services with costs found!")
            return
        
        # Step 2: Map to CloudWatch namespaces
        mapped_namespaces = self.map_services_to_namespaces(services_with_cost)
        
        # Step 3-7: Discover metrics and create tables
        total_tables = 0
        total_datapoints = 0
        created_tables = []
        
        for service, namespace in mapped_namespaces.items():
            cost = services_with_cost[service]
            
            # Discover all metrics
            metrics = self.discover_metrics(namespace)
            if not metrics:
                continue
            
            # Filter and rank
            top_metrics = self.filter_and_rank_metrics(metrics)
            print(f"\n   📈 Processing top {len(top_metrics)} metrics for {service}")
            
            for item in top_metrics:
                metric = item['metric']
                metric_name = metric['MetricName']
                dimensions = metric.get('Dimensions', [])
                
                # Create table name
                table_name = self.create_table_name(service, metric_name)
                
                print(f"\n   🔧 Creating table: {table_name}")
                
                # Create metric table
                self.create_metric_table(table_name)
                
                # Fetch 30 days of data
                datapoints = self.fetch_metric_statistics(
                    namespace, metric_name, dimensions, days=30
                )
                
                if datapoints:
                    # Get unit from first datapoint
                    unit = datapoints[0].get('Unit', 'None')
                    
                    # Store data in table
                    stored = self.store_metric_data(
                        table_name, datapoints, dimensions, unit
                    )
                    
                    # Register in catalog
                    self.register_in_catalog(
                        table_name, service, namespace, metric_name,
                        dimensions, cost, item['score'], stored
                    )
                    
                    total_datapoints += stored
                    total_tables += 1
                    created_tables.append(table_name)
        
        print("\n" + "=" * 70)
        print(f"✅ COMPLETE: {total_tables} tables created, {total_datapoints} datapoints stored")
        print(f"📂 Database: {self.db_name}")
        print(f"📊 Schema: {self.schema_name}")
        print("=" * 70)
        
        self.print_summary(created_tables)
    
    def print_summary(self, created_tables):
        """Print database summary"""
        cursor = self.conn.cursor()
        
        print("\n📊 DATABASE SUMMARY:")
        
        # Total tables
        cursor.execute("SELECT COUNT(*) FROM cloudwatch_metrics_catalog")
        total = cursor.fetchone()[0]
        print(f"   • Total metric tables: {total}")
        
        # Total datapoints
        cursor.execute("SELECT SUM(record_count) FROM cloudwatch_metrics_catalog")
        total_dp = cursor.fetchone()[0] or 0
        print(f"   • Total datapoints: {total_dp:,}")
        
        # Services
        cursor.execute("SELECT COUNT(DISTINCT service_name) FROM cloudwatch_metrics_catalog")
        svc_count = cursor.fetchone()[0]
        print(f"   • Unique services: {svc_count}")
        
        # Top services by cost
        print("\n   📋 Created Tables by Service:")
        cursor.execute('''
            SELECT service_name, COUNT(*) as table_count, 
                   AVG(service_cost) as avg_cost,
                   SUM(record_count) as total_records
            FROM cloudwatch_metrics_catalog
            GROUP BY service_name
            ORDER BY avg_cost DESC
        ''')
        for row in cursor.fetchall():
            print(f"      • {row[0]}: {row[1]} tables, ${row[2]:.2f}, {row[3]:,} records")
        
        # Sample tables
        print("\n   📊 Sample Tables Created:")
        for table in created_tables[:10]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"      • {table}: {count:,} records")
        
        print("\n   💡 Query Examples:")
        if created_tables:
            sample_table = created_tables[0]
            print(f"      • SELECT * FROM {sample_table} LIMIT 10;")
            print(f"      • SELECT AVG(average) FROM {sample_table};")
            print(f"      • SELECT * FROM cloudwatch_metrics_catalog;")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    # Initialize discovery
    discovery = AWSCostMetricDiscovery(
        region='us-east-1',
        top_n_metrics=10,
        db_name='aws_metrics.db'
    )
    
    try:
        # Run full pipeline
        discovery.run()
    finally:
        discovery.close()
    
    print("\n✅ Discovery complete! Check aws_metrics.db")
    print("   Tables follow format: cloudwatch_metrics_{service}_{metric}")