"""
AWS Cost Explorer + CloudWatch Metric Discovery with PostgreSQL
Creates schema 'cloudwatch_metrics' with tables: {service_name}_{metric_name}
"""

import boto3
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import json
import re

class AWSCostMetricDiscovery:
    def __init__(self, db_config, profile_name='finops', region='us-east-1', top_n_metrics=10):
        self.session = boto3.Session(profile_name=profile_name)
        self.ce_client = self.session.client('ce', region_name=region)
        self.cw_client = self.session.client('cloudwatch', region_name=region)
        
        self.db_config = db_config
        self.region = region
        self.top_n_metrics = top_n_metrics
        self.conn = None
        self.schema = 'cloudwatch_metrics'
        
        self.service_to_namespace = {
            'Amazon Elastic Compute Cloud - Compute': 'AWS/EC2',
            'EC2 - Other': 'AWS/EC2',
            'Amazon Simple Storage Service': 'AWS/S3',
            'Amazon Relational Database Service': 'AWS/RDS',
            'AWS Lambda': 'AWS/Lambda',
            'Amazon DynamoDB': 'AWS/DynamoDB',
            'Application Load Balancer': 'AWS/ApplicationELB',
            'Amazon CloudFront': 'AWS/CloudFront',
            'Amazon ElastiCache': 'AWS/ElastiCache',
            'Amazon ECS': 'AWS/ECS',
            'Amazon EKS': 'AWS/EKS',
        }
        
        # Business-relevant metric patterns
        self.priority_patterns = [
            r'(?i)(CPUUtilization|NetworkIn|disk|storage).*util',
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
        
        self.priority_metrics = {
            'AWS/EC2': [
                'CPUUtilization',
                'NetworkIn',
                'NetworkOut',
                'DiskReadBytes',
                'DiskWriteBytes'
            ],
            'AWS/RDS': [
                'CPUUtilization',
                'DatabaseConnections',
                'ReadLatency',
                'WriteLatency',
                'FreeStorageSpace'
            ],
            'AWS/Lambda': [
                'Invocations',
                'Duration',
                'Errors',
                'Throttles',
                'ConcurrentExecutions'
            ],
            'AWS/S3': [
                'BucketSizeBytes',
                'NumberOfObjects',
                'AllRequests',
                '4xxErrors',
                '5xxErrors'
            ],
            'AWS/VPC': [
                'NetworkPacketsIn',
                'NetworkPacketsOut',
                'NetworkBytesIn',
                'NetworkBytesOut',
                'PublicIPAddresses',
            ]
        }

        # Fallback patterns for services not in the priority list
        self.priority_patterns = [
            r'(?i)(cpu|memory|disk|storage).*util',
            r'(?i)utilization',
            r'(?i)(active|concurrent|network).*connection',
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

        # Add all specific priority metric names as case-insensitive regex patterns
        all_metrics = [metric for metrics in self.priority_metrics.values() for metric in metrics]
        metric_patterns = [rf'(?i){re.escape(metric)}' for metric in all_metrics]
        self.priority_patterns.extend(metric_patterns)

        self.exclude_patterns = [
            r'(?i)billing',
            r'(?i)quota',
            r'(?i)estimated.*charge',
            r'(?i)free.*tier',
        ]
    
    
    def connect(self):
        self.conn = psycopg2.connect(**self.db_config)
        self.conn.autocommit = False
    
    def init_schema(self):
        print(f"🗄️  Initializing schema: {self.schema}")
        with self.conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.catalog (
                    id SERIAL PRIMARY KEY,
                    table_name TEXT UNIQUE NOT NULL,
                    service_name TEXT NOT NULL,
                    namespace TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    dimensions JSONB,
                    service_cost NUMERIC(12,2),
                    relevance_score INT,
                    record_count INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        self.conn.commit()
        print("✅ Schema initialized")
    
    def sanitize_name(self, text):
        clean = re.sub(r'[^a-zA-Z0-9]', '_', text)
        clean = re.sub(r'_+', '_', clean).strip('_').lower()
        return clean[:50]  # Limit length
    
    def create_table(self, service, metric_name):
        table = f"{self.sanitize_name(service)}_{self.sanitize_name(metric_name)}"
        full_name = f"{self.schema}.{table}"
        
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {full_name} (
                    id SERIAL PRIMARY KEY,
                    ts TIMESTAMPTZ NOT NULL,
                    avg DOUBLE PRECISION,
                    sum DOUBLE PRECISION,
                    min DOUBLE PRECISION,
                    max DOUBLE PRECISION,
                    sample_count DOUBLE PRECISION,
                    unit TEXT,
                    dims JSONB,
                    UNIQUE(ts, dims)
                )
            """)
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_ts ON {full_name}(ts)")
        self.conn.commit()
        return table
    
    def get_services_with_costs(self, months=6):
        print(f"🔍 Querying Cost Explorer ({months}m)...")
        end = datetime.now().date()
        start = end - timedelta(days=30 * months)
        
        resp = self.ce_client.get_cost_and_usage(
            TimePeriod={'Start': start.strftime('%Y-%m-%d'), 'End': end.strftime('%Y-%m-%d')},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        costs = {}
        for result in resp['ResultsByTime']:
            for group in result['Groups']:
                svc = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if cost > 0:
                    costs[svc] = costs.get(svc, 0) + cost
        
        sorted_costs = dict(sorted(costs.items(), key=lambda x: x[1], reverse=True))
        print(f"✅ Found {len(sorted_costs)} services with costs")
        return sorted_costs
    
    def discover_metrics(self, namespace):
        metrics = []
        paginator = self.cw_client.get_paginator('list_metrics')
        try:
            for page in paginator.paginate(Namespace=namespace):
                metrics.extend(page['Metrics'])
        except Exception as e:
            print(f"❌ Error: {e}")
        return metrics
    
    def score_metric(self, name):
        score = sum(10 for p in self.priority_patterns if re.search(p, name))
        return score if score > 0 else 0
    
    def fetch_stats(self, namespace, metric_name, dimensions, days=30):
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        try:
            resp = self.cw_client.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start,
                EndTime=end,
                Period=3600,
                Statistics=['Average', 'Sum', 'Minimum', 'Maximum', 'SampleCount']
            )
            return resp.get('Datapoints', [])
        except Exception as e:
            print(f"❌ {e}")
            return []
    
    def store_data(self, table, datapoints, dimensions):
        if not datapoints:
            return 0
        
        full_name = f"{self.schema}.{table}"
        dims_json = json.dumps(dimensions) if dimensions else None
        
        values = [(
            dp['Timestamp'], dp.get('Average'), dp.get('Sum'),
            dp.get('Minimum'), dp.get('Maximum'), dp.get('SampleCount'),
            dp.get('Unit', 'None'), dims_json
        ) for dp in datapoints]
        
        with self.conn.cursor() as cur:
            execute_values(cur, f"""
                INSERT INTO {full_name} (ts, avg, sum, min, max, sample_count, unit, dims)
                VALUES %s ON CONFLICT (ts, dims) DO NOTHING
            """, values)
        self.conn.commit()
        return len(values)
    
    def register_catalog(self, table, service, namespace, metric, dims, cost, score, count):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self.schema}.catalog 
                (table_name, service_name, namespace, metric_name, dimensions, 
                 service_cost, relevance_score, record_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (table_name) DO UPDATE SET record_count = EXCLUDED.record_count
            """, (table, service, namespace, metric, json.dumps(dims) if dims else None, 
                  cost, score, count))
        self.conn.commit()
    
    def run(self):
        print("=" * 70)
        print("AWS COST + CLOUDWATCH DISCOVERY - POSTGRESQL")
        print("=" * 70)
        
        self.connect()
        self.init_schema()
        
        costs = self.get_services_with_costs()
        if not costs:
            return
        
        total_tables = 0
        total_points = 0
        
        for service, cost in costs.items():
            namespace = self.service_to_namespace.get(service)
            if not namespace:
                continue
            
            print(f"\n📊 {service} → {namespace}")
            metrics = self.discover_metrics(namespace)
            if not metrics:
                continue
            
            scored = [(m, self.score_metric(m['MetricName'])) for m in metrics]
            top = sorted([s for s in scored if s[1] > 0], key=lambda x: x[1], reverse=True)[:self.top_n_metrics]
            
            for metric, score in top:
                name = metric['MetricName']
                dims = metric.get('Dimensions', [])
                
                table = self.create_table(service, name)
                print(f"  🔧 {table}")
                
                points = self.fetch_stats(namespace, name, dims)
                if points:
                    stored = self.store_data(table, points, dims)
                    self.register_catalog(table, service, namespace, name, dims, cost, score, stored)
                    total_tables += 1
                    total_points += stored
        
        print(f"\n✅ Created {total_tables} tables, {total_points:,} datapoints")
        self.print_summary()
    
    def print_summary(self):
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*), SUM(record_count) FROM {self.schema}.catalog")
            tables, points = cur.fetchone()
            print(f"\n📊 Total: {tables} tables, {points:,} records")
            
            cur.execute(f"""
                SELECT service_name, COUNT(*), SUM(record_count)
                FROM {self.schema}.catalog
                GROUP BY service_name ORDER BY SUM(record_count) DESC LIMIT 5
            """)
            print("\n🏆 Top Services:")
            for svc, cnt, recs in cur.fetchall():
                print(f"  • {svc}: {cnt} tables, {recs:,} records")
    
    def export_to_sql(self, filename='aws_metrics_export.sql'):
        """Export entire schema to SQL file"""
        print(f"\n📥 Exporting to {filename}...")
        
        with open(filename, 'w') as f:
            # Header
            f.write(f"-- AWS CloudWatch Metrics Export\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Schema: {self.schema}\n\n")
            
            # Create schema
            f.write(f"CREATE SCHEMA IF NOT EXISTS {self.schema};\n\n")
            
            with self.conn.cursor() as cur:
                # Get all tables in schema
                cur.execute(f"""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, (self.schema,))
                
                tables = [row[0] for row in cur.fetchall()]
                
                for table in tables:
                    full_name = f"{self.schema}.{table}"
                    f.write(f"-- Table: {full_name}\n")
                    
                    # Get CREATE TABLE statement
                    cur.execute(f"""
                        SELECT column_name, data_type, character_maximum_length,
                            column_default, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                    """, (self.schema, table))
                    
                    cols = cur.fetchall()
                    
                    # Build CREATE TABLE
                    f.write(f"CREATE TABLE IF NOT EXISTS {full_name} (\n")
                    col_defs = []
                    for col_name, dtype, max_len, default, nullable in cols:
                        col_def = f"    {col_name} {dtype}"
                        if max_len:
                            col_def += f"({max_len})"
                        if default:
                            col_def += f" DEFAULT {default}"
                        if nullable == 'NO':
                            col_def += " NOT NULL"
                        col_defs.append(col_def)
                    f.write(",\n".join(col_defs))
                    f.write("\n);\n\n")
                    
                    # Get indexes
                    cur.execute(f"""
                        SELECT indexname, indexdef 
                        FROM pg_indexes 
                        WHERE schemaname = %s AND tablename = %s
                    """, (self.schema, table))
                    
                    for idx_name, idx_def in cur.fetchall():
                        if 'pkey' not in idx_name.lower():
                            f.write(f"{idx_def};\n")
                    
                    # Export data
                    cur.execute(f"SELECT COUNT(*) FROM {full_name}")
                    count = cur.fetchone()[0]
                    
                    if count > 0:
                        f.write(f"\n-- Data for {table} ({count:,} rows)\n")
                        
                        # Get column names and types
                        cur.execute(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position
                        """, (self.schema, table))
                        
                        col_info = cur.fetchall()
                        col_names = [c[0] for c in col_info]
                        col_types = {c[0]: c[1] for c in col_info}
                        
                        # Export in batches
                        batch_size = 1000
                        cur.execute(f"SELECT * FROM {full_name}")
                        
                        while True:
                            rows = cur.fetchmany(batch_size)
                            if not rows:
                                break
                            
                            for row in rows:
                                values = []
                                for idx, val in enumerate(row):
                                    col_name = col_names[idx]
                                    col_type = col_types[col_name]
                                    
                                    if val is None:
                                        values.append('NULL')
                                    elif col_type == 'jsonb':
                                        # For JSONB, use dollar-quoted strings to avoid escaping issues
                                        json_str = json.dumps(val)
                                        # Use dollar quoting to avoid escaping issues
                                        values.append(f"$${json_str}$$::jsonb")
                                    elif isinstance(val, (int, float)):
                                        values.append(str(val))
                                    elif isinstance(val, datetime):
                                        values.append(f"'{val.isoformat()}'")
                                    else:
                                        # For regular strings, escape single quotes
                                        escaped = str(val).replace("'", "''")
                                        values.append(f"'{escaped}'")
                                
                                f.write(f"INSERT INTO {full_name} ({', '.join(col_names)}) ")
                                f.write(f"VALUES ({', '.join(values)});\n")
                    
                    f.write("\n\n")
        
        print(f"✅ Exported to {filename}")
        
        # Print file size
        import os
        size_mb = os.path.getsize(filename) / (1024 * 1024)
        print(f"📊 File size: {size_mb:.2f} MB")

    def close(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'postgres',
        'port': 5432
    }
    
    discovery = AWSCostMetricDiscovery(db_config, region='us-east-1', top_n_metrics=10)
    try:
        discovery.run()
        
        # Export to SQL file
        discovery.export_to_sql('aws_metrics_export.sql')

        
    finally:
        discovery.close()
    
    print("\n✅ Complete! Query: SELECT * FROM cloudwatch_metrics.catalog;")