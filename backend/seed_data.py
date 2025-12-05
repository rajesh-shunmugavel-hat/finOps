import os
import sys
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models.models import (
    Department, Service, Resource,
    EC2Metric, RDSMetric, S3Metric, LambdaMetric,
    AIReport, Recommendation, MonthlyCostHistory
)

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        departments = [
            Department(name="Engineering", monthly_budget=10000, cost_center="ENG-001"),
            Department(name="Data Science", monthly_budget=5000, cost_center="DS-001"),
            Department(name="Infrastructure", monthly_budget=4000, cost_center="INF-001"),
            Department(name="DevOps", monthly_budget=3000, cost_center="DEV-001"),
        ]
        db.add_all(departments)
        db.flush()
        
        services = [
            Service(name="EC2", service_type="Compute", monthly_cost=6939, category="Core", description="Elastic Compute Cloud instances"),
            Service(name="RDS", service_type="Database", monthly_cost=3855, category="Core", description="Relational Database Service"),
            Service(name="S3", service_type="Storage", monthly_cost=2313, category="Storage", description="Simple Storage Service"),
            Service(name="Lambda", service_type="Compute", monthly_cost=1542, category="Serverless", description="Serverless compute functions"),
            Service(name="Other", service_type="Various", monthly_cost=771, category="Other", description="Other AWS services"),
        ]
        db.add_all(services)
        db.flush()
        
        ec2_resources = [
            {"name": "prod-web-01", "type": "t3.large", "cost": 150, "dept": "Engineering", "cpu": 8, "mem": 12},
            {"name": "prod-web-02", "type": "t3.large", "cost": 150, "dept": "Engineering", "cpu": 7, "mem": 10},
            {"name": "prod-web-03", "type": "t3.large", "cost": 150, "dept": "Engineering", "cpu": 5, "mem": 8},
            {"name": "prod-api-01", "type": "t3.xlarge", "cost": 300, "dept": "Engineering", "cpu": 35, "mem": 40},
            {"name": "prod-api-02", "type": "t3.xlarge", "cost": 300, "dept": "Engineering", "cpu": 38, "mem": 42},
            {"name": "prod-db-backup", "type": "t3.xlarge", "cost": 300, "dept": "Infrastructure", "cpu": 0.5, "mem": 1},
            {"name": "staging-web-01", "type": "t3.medium", "cost": 75, "dept": "DevOps", "cpu": 3, "mem": 5},
            {"name": "staging-api-01", "type": "t3.medium", "cost": 75, "dept": "DevOps", "cpu": 4, "mem": 6},
            {"name": "ml-training-01", "type": "p3.2xlarge", "cost": 2500, "dept": "Data Science", "cpu": 85, "mem": 78},
            {"name": "ml-inference-01", "type": "g4dn.xlarge", "cost": 800, "dept": "Data Science", "cpu": 60, "mem": 55},
            {"name": "batch-processor", "type": "c5.2xlarge", "cost": 400, "dept": "Engineering", "cpu": 12, "mem": 15},
            {"name": "dev-instance-01", "type": "t3.micro", "cost": 15, "dept": "Engineering", "cpu": 2, "mem": 3},
            {"name": "monitoring-server", "type": "t3.small", "cost": 35, "dept": "Infrastructure", "cpu": 45, "mem": 50},
            {"name": "bastion-host", "type": "t3.nano", "cost": 8, "dept": "Infrastructure", "cpu": 1, "mem": 2},
            {"name": "log-aggregator", "type": "t3.medium", "cost": 75, "dept": "Infrastructure", "cpu": 55, "mem": 65},
            {"name": "cache-server", "type": "r5.large", "cost": 180, "dept": "Engineering", "cpu": 25, "mem": 70},
            {"name": "test-runner", "type": "t3.large", "cost": 150, "dept": "DevOps", "cpu": 10, "mem": 12},
            {"name": "ci-agent-01", "type": "t3.medium", "cost": 75, "dept": "DevOps", "cpu": 65, "mem": 55},
            {"name": "ci-agent-02", "type": "t3.medium", "cost": 75, "dept": "DevOps", "cpu": 70, "mem": 60},
            {"name": "analytics-server", "type": "m5.xlarge", "cost": 350, "dept": "Data Science", "cpu": 40, "mem": 45},
        ]
        
        ec2_service = next(s for s in services if s.name == "EC2")
        for ec2_data in ec2_resources:
            dept = next((d for d in departments if d.name == ec2_data["dept"]), departments[0])
            resource = Resource(
                service_id=ec2_service.id,
                department_id=dept.id,
                resource_name=ec2_data["name"],
                resource_type="Instance",
                instance_type=ec2_data["type"],
                monthly_cost=ec2_data["cost"],
                region="us-east-1",
                status="running"
            )
            db.add(resource)
            db.flush()
            
            for i in range(24):
                timestamp = datetime.now() - timedelta(hours=i)
                cpu_var = random.uniform(-2, 2)
                mem_var = random.uniform(-3, 3)
                metric = EC2Metric(
                    resource_id=resource.id,
                    cpu_utilization=max(0, min(100, ec2_data["cpu"] + cpu_var)),
                    cpu_credit_usage=random.uniform(0, 50),
                    memory_utilization=max(0, min(100, ec2_data["mem"] + mem_var)),
                    network_in=random.uniform(1000000, 50000000),
                    network_out=random.uniform(500000, 25000000),
                    disk_read_ops=random.uniform(100, 5000),
                    disk_write_ops=random.uniform(50, 2500),
                    disk_read_bytes=random.uniform(1000000, 100000000),
                    disk_write_bytes=random.uniform(500000, 50000000),
                    status_check_failed=0,
                    timestamp=timestamp
                )
                db.add(metric)
        
        rds_resources = [
            {"name": "prod-postgres-primary", "type": "db.r5.xlarge", "cost": 1800, "dept": "Engineering", "cpu": 72, "conn": 150, "storage": 500000000000},
            {"name": "prod-postgres-replica", "type": "db.r5.large", "cost": 900, "dept": "Engineering", "cpu": 45, "conn": 80, "storage": 500000000000},
            {"name": "prod-mysql-analytics", "type": "db.m5.large", "cost": 450, "dept": "Data Science", "cpu": 55, "conn": 40, "storage": 200000000000},
            {"name": "staging-postgres", "type": "db.t3.medium", "cost": 150, "dept": "DevOps", "cpu": 15, "conn": 5, "storage": 50000000000},
            {"name": "dev-postgres", "type": "db.t3.small", "cost": 75, "dept": "Engineering", "cpu": 8, "conn": 3, "storage": 20000000000},
            {"name": "reporting-mysql", "type": "db.m5.xlarge", "cost": 480, "dept": "Data Science", "cpu": 35, "conn": 25, "storage": 300000000000},
        ]
        
        rds_service = next(s for s in services if s.name == "RDS")
        for rds_data in rds_resources:
            dept = next((d for d in departments if d.name == rds_data["dept"]), departments[0])
            resource = Resource(
                service_id=rds_service.id,
                department_id=dept.id,
                resource_name=rds_data["name"],
                resource_type="Database",
                instance_type=rds_data["type"],
                monthly_cost=rds_data["cost"],
                region="us-east-1",
                status="available"
            )
            db.add(resource)
            db.flush()
            
            for i in range(24):
                timestamp = datetime.now() - timedelta(hours=i)
                metric = RDSMetric(
                    resource_id=resource.id,
                    cpu_utilization=rds_data["cpu"] + random.uniform(-5, 5),
                    database_connections=int(rds_data["conn"] + random.randint(-10, 10)),
                    free_storage_space=rds_data["storage"] * random.uniform(0.3, 0.7),
                    freeable_memory=random.uniform(1000000000, 8000000000),
                    read_latency=random.uniform(0.001, 0.01),
                    write_latency=random.uniform(0.002, 0.02),
                    read_iops=random.uniform(100, 2000),
                    write_iops=random.uniform(50, 1000),
                    network_receive_throughput=random.uniform(1000000, 10000000),
                    network_transmit_throughput=random.uniform(500000, 5000000),
                    timestamp=timestamp
                )
                db.add(metric)
        
        s3_resources = [
            {"name": "prod-media-assets", "size": 2000000000000, "objects": 500000, "requests": 50000, "dept": "Engineering"},
            {"name": "prod-user-uploads", "size": 800000000000, "objects": 200000, "requests": 25000, "dept": "Engineering"},
            {"name": "data-lake-raw", "size": 5000000000000, "objects": 1000000, "requests": 500, "dept": "Data Science"},
            {"name": "data-lake-processed", "size": 1500000000000, "objects": 300000, "requests": 2000, "dept": "Data Science"},
            {"name": "backup-daily", "size": 3000000000000, "objects": 50000, "requests": 100, "dept": "Infrastructure"},
            {"name": "backup-weekly", "size": 2000000000000, "objects": 10000, "requests": 50, "dept": "Infrastructure"},
            {"name": "logs-archive", "size": 1000000000000, "objects": 800000, "requests": 200, "dept": "DevOps"},
            {"name": "static-website", "size": 50000000000, "objects": 5000, "requests": 100000, "dept": "Engineering"},
            {"name": "ml-models", "size": 500000000000, "objects": 1000, "requests": 5000, "dept": "Data Science"},
            {"name": "temp-processing", "size": 200000000000, "objects": 50000, "requests": 15000, "dept": "Engineering"},
        ]
        
        s3_service = next(s for s in services if s.name == "S3")
        s3_total = 0
        for s3_data in s3_resources:
            size_gb = s3_data["size"] / (1024**3)
            cost = size_gb * 0.023 + (s3_data["requests"] * 0.0004)
            s3_total += cost
            
            dept = next((d for d in departments if d.name == s3_data["dept"]), departments[0])
            resource = Resource(
                service_id=s3_service.id,
                department_id=dept.id,
                resource_name=s3_data["name"],
                resource_type="Bucket",
                instance_type="Standard",
                monthly_cost=round(cost, 2),
                region="us-east-1",
                status="active"
            )
            db.add(resource)
            db.flush()
            
            for i in range(24):
                timestamp = datetime.now() - timedelta(hours=i)
                metric = S3Metric(
                    resource_id=resource.id,
                    bucket_size_bytes=s3_data["size"],
                    number_of_objects=s3_data["objects"],
                    all_requests=int(s3_data["requests"] / 24),
                    get_requests=int(s3_data["requests"] / 24 * 0.7),
                    put_requests=int(s3_data["requests"] / 24 * 0.2),
                    delete_requests=int(s3_data["requests"] / 24 * 0.1),
                    bytes_downloaded=random.uniform(1000000000, 50000000000),
                    bytes_uploaded=random.uniform(500000000, 25000000000),
                    first_byte_latency=random.uniform(10, 100),
                    errors_4xx=random.randint(0, 10),
                    errors_5xx=random.randint(0, 2),
                    timestamp=timestamp
                )
                db.add(metric)
        
        lambda_resources = [
            {"name": "api-auth-handler", "invocations": 50000, "duration": 150, "errors": 50, "dept": "Engineering"},
            {"name": "image-processor", "invocations": 15000, "duration": 2500, "errors": 20, "dept": "Engineering"},
            {"name": "data-etl-job", "invocations": 500, "duration": 45000, "errors": 5, "dept": "Data Science"},
            {"name": "notification-sender", "invocations": 25000, "duration": 200, "errors": 100, "dept": "Engineering"},
            {"name": "backup-trigger", "invocations": 30, "duration": 5000, "errors": 0, "dept": "Infrastructure"},
            {"name": "log-processor", "invocations": 100000, "duration": 100, "errors": 200, "dept": "DevOps"},
            {"name": "health-checker", "invocations": 8640, "duration": 50, "errors": 10, "dept": "Infrastructure"},
            {"name": "report-generator", "invocations": 100, "duration": 30000, "errors": 2, "dept": "Data Science"},
            {"name": "cache-warmer", "invocations": 1440, "duration": 500, "errors": 5, "dept": "Engineering"},
            {"name": "cleanup-job", "invocations": 30, "duration": 10000, "errors": 0, "dept": "Infrastructure"},
            {"name": "webhook-receiver", "invocations": 5000, "duration": 100, "errors": 25, "dept": "Engineering"},
            {"name": "ml-inference", "invocations": 10000, "duration": 800, "errors": 50, "dept": "Data Science"},
        ]
        
        lambda_service = next(s for s in services if s.name == "Lambda")
        for lambda_data in lambda_resources:
            gb_seconds = (lambda_data["invocations"] * lambda_data["duration"]) / 1000 * 0.5
            cost = (gb_seconds * 0.0000166667) + (lambda_data["invocations"] * 0.0000002)
            
            dept = next((d for d in departments if d.name == lambda_data["dept"]), departments[0])
            resource = Resource(
                service_id=lambda_service.id,
                department_id=dept.id,
                resource_name=lambda_data["name"],
                resource_type="Function",
                instance_type="128MB",
                monthly_cost=round(cost, 2),
                region="us-east-1",
                status="active"
            )
            db.add(resource)
            db.flush()
            
            for i in range(24):
                timestamp = datetime.now() - timedelta(hours=i)
                hourly_invocations = int(lambda_data["invocations"] / 720)
                metric = LambdaMetric(
                    resource_id=resource.id,
                    invocations=hourly_invocations + random.randint(-10, 10),
                    duration_avg=lambda_data["duration"] + random.uniform(-50, 50),
                    duration_max=lambda_data["duration"] * 1.5,
                    errors=int(lambda_data["errors"] / 720) + random.randint(0, 2),
                    throttles=random.randint(0, 5),
                    concurrent_executions=random.randint(1, 50),
                    dead_letter_errors=random.randint(0, 1),
                    iterator_age=random.uniform(0, 1000),
                    provisioned_concurrency_invocations=0,
                    timestamp=timestamp
                )
                db.add(metric)
        
        months = ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11"]
        base_costs = {
            "EC2": [6200, 6500, 6700, 6800, 6939],
            "RDS": [3600, 3700, 3750, 3800, 3855],
            "S3": [2100, 2200, 2250, 2280, 2313],
            "Lambda": [1500, 1550, 1520, 1530, 1542],
            "Other": [800, 850, 880, 890, 771],
        }
        
        for i, month in enumerate(months):
            year, m = month.split("-")
            for service in services:
                if service.name in base_costs:
                    history = MonthlyCostHistory(
                        service_id=service.id,
                        month=m,
                        year=int(year),
                        total_cost=base_costs[service.name][i]
                    )
                    db.add(history)
        
        report = AIReport(
            analysis_date=datetime.now() - timedelta(days=7),
            total_current_spend=15420,
            total_monthly_savings=3000,
            optimization_count=5,
            status="Optimization Opportunities Found",
            executive_summary="Total identified savings: $3,000/month (19.5% reduction). Found 5 optimization opportunities across 4 AWS services. Highest ROI opportunities: EC2 right-sizing and S3 tiering. Recommended implementation timeline: 2 weeks."
        )
        db.add(report)
        db.flush()
        
        sample_recommendations = [
            Recommendation(
                report_id=report.id,
                service_name="EC2",
                resource_name="prod-web-01, prod-web-02, prod-web-03",
                finding_title="Underutilized Web Server Instances",
                justification_status="NOT_JUSTIFIED",
                issue_description="3 t3.large instances are running 24/7 with average CPU utilization below 8%. Memory utilization is also low at 10-12%.",
                recommendation_text="Downsize from t3.large to t3.micro (saves $1,800/month) or implement Auto Scaling to match demand. Consider using Spot Instances for non-production workloads.",
                estimated_monthly_savings=1350,
                roi_percentage=100,
                implementation_effort_hours=2,
                department_name="Engineering"
            ),
            Recommendation(
                report_id=report.id,
                service_name="EC2",
                resource_name="prod-db-backup",
                finding_title="Severely Underutilized Backup Instance",
                justification_status="NOT_JUSTIFIED",
                issue_description="t3.xlarge instance running with 0.5% CPU and 1% memory utilization. This instance appears to be idle most of the time.",
                recommendation_text="Terminate this instance and use AWS Backup for RDS backups instead, or downsize to t3.nano if occasional compute is needed.",
                estimated_monthly_savings=285,
                roi_percentage=95,
                implementation_effort_hours=1,
                department_name="Infrastructure"
            ),
            Recommendation(
                report_id=report.id,
                service_name="RDS",
                resource_name="prod-postgres-primary",
                finding_title="Well Utilized Production Database",
                justification_status="JUSTIFIED",
                issue_description="RDS instance running at 72% CPU with 150 active connections, indicating appropriate sizing for production workload.",
                recommendation_text="No changes recommended. Consider enabling Performance Insights for detailed query analysis.",
                estimated_monthly_savings=0,
                roi_percentage=0,
                implementation_effort_hours=0,
                department_name="Engineering"
            ),
            Recommendation(
                report_id=report.id,
                service_name="S3",
                resource_name="data-lake-raw, backup-daily, backup-weekly",
                finding_title="Infrequently Accessed Storage",
                justification_status="PARTIALLY_JUSTIFIED",
                issue_description="10TB of data across 3 buckets with fewer than 700 requests/month, suggesting infrequent access patterns.",
                recommendation_text="Enable S3 Intelligent-Tiering to automatically move data between access tiers. For backup buckets, transition to S3 Glacier after 30 days.",
                estimated_monthly_savings=1200,
                roi_percentage=52,
                implementation_effort_hours=1,
                department_name="Data Science"
            ),
            Recommendation(
                report_id=report.id,
                service_name="Lambda",
                resource_name="backup-trigger, cleanup-job",
                finding_title="Low Usage Lambda Functions",
                justification_status="PARTIALLY_JUSTIFIED",
                issue_description="Two Lambda functions with fewer than 60 invocations/month combined, but they serve essential maintenance purposes.",
                recommendation_text="Review if these functions can be consolidated. Consider using AWS EventBridge Scheduler instead of dedicated Lambda functions for simple scheduled tasks.",
                estimated_monthly_savings=165,
                roi_percentage=70,
                implementation_effort_hours=0.5,
                department_name="Infrastructure"
            ),
        ]
        db.add_all(sample_recommendations)
        
        db.commit()
        print("Database seeded successfully!")
        print(f"Created {len(departments)} departments")
        print(f"Created {len(services)} services")
        print(f"Created {len(ec2_resources)} EC2 instances with 24h of metrics each")
        print(f"Created {len(rds_resources)} RDS instances with 24h of metrics each")
        print(f"Created {len(s3_resources)} S3 buckets with 24h of metrics each")
        print(f"Created {len(lambda_resources)} Lambda functions with 24h of metrics each")
        print(f"Created {len(months)} months of cost history")
        print(f"Created 1 sample AI report with {len(sample_recommendations)} recommendations")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
