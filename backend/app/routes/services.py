from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models.models import (
    Service, Resource, Department,
    EC2Metric, RDSMetric, S3Metric, LambdaMetric
)
from ..models.schemas import (
    ServiceResponse, ServiceDrilldown, ResourceWithMetrics,
    EC2MetricResponse, RDSMetricResponse, S3MetricResponse, LambdaMetricResponse
)

router = APIRouter(prefix="/api", tags=["services"])

def get_utilization_status(service_type: str, metrics: dict) -> str:
    if service_type == "EC2":
        cpu = metrics.get("cpu_utilization", 0)
        if cpu < 10:
            return "Severely Underutilized"
        elif cpu < 30:
            return "Underutilized"
        elif cpu < 70:
            return "Optimally Utilized"
        else:
            return "Highly Utilized"
    elif service_type == "RDS":
        cpu = metrics.get("cpu_utilization", 0)
        connections = metrics.get("database_connections", 0)
        if cpu < 20 and connections < 5:
            return "Underutilized"
        elif cpu > 80:
            return "Highly Utilized"
        else:
            return "Optimally Utilized"
    elif service_type == "S3":
        requests = metrics.get("all_requests", 0)
        if requests < 100:
            return "Low Activity"
        elif requests < 10000:
            return "Moderate Activity"
        else:
            return "High Activity"
    elif service_type == "Lambda":
        invocations = metrics.get("invocations", 0)
        errors = metrics.get("errors", 0)
        error_rate = (errors / invocations * 100) if invocations > 0 else 0
        if invocations < 100:
            return "Low Usage"
        elif error_rate > 5:
            return "High Error Rate"
        else:
            return "Healthy"
    return "Unknown"

@router.get("/services", response_model=List[ServiceResponse])
def get_all_services(db: Session = Depends(get_db)):
    services = db.query(Service).all()
    total_spend = sum(s.monthly_cost for s in services)
    
    return [
        ServiceResponse(
            id=s.id,
            name=s.name,
            service_type=s.service_type,
            monthly_cost=s.monthly_cost,
            category=s.category,
            percentage_of_total=round((s.monthly_cost / total_spend * 100), 1) if total_spend > 0 else 0,
            resource_count=db.query(Resource).filter(Resource.service_id == s.id).count()
        )
        for s in services
    ]

@router.get("/services/{service_name}", response_model=ServiceDrilldown)
def get_service_drilldown(service_name: str, db: Session = Depends(get_db)):
    service = db.query(Service).filter(
        func.lower(Service.name) == service_name.lower()
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    resources = db.query(Resource).filter(Resource.service_id == service.id).all()
    total_spend = db.query(func.sum(Service.monthly_cost)).scalar() or 0
    
    resource_responses = []
    for resource in resources:
        dept_name = resource.department.name if resource.department else None
        
        resource_data = ResourceWithMetrics(
            id=resource.id,
            resource_name=resource.resource_name,
            resource_type=resource.resource_type,
            instance_type=resource.instance_type,
            monthly_cost=resource.monthly_cost,
            region=resource.region,
            status=resource.status,
            service_name=service.name,
            department_name=dept_name,
            utilization_status="Unknown"
        )
        
        if service.name == "EC2":
            metric = db.query(EC2Metric).filter(
                EC2Metric.resource_id == resource.id
            ).order_by(EC2Metric.timestamp.desc()).first()
            if metric:
                resource_data.ec2_metrics = EC2MetricResponse(
                    cpu_utilization=metric.cpu_utilization,
                    cpu_credit_usage=metric.cpu_credit_usage,
                    memory_utilization=metric.memory_utilization,
                    network_in=metric.network_in,
                    network_out=metric.network_out,
                    disk_read_ops=metric.disk_read_ops,
                    disk_write_ops=metric.disk_write_ops,
                    disk_read_bytes=metric.disk_read_bytes,
                    disk_write_bytes=metric.disk_write_bytes,
                    status_check_failed=metric.status_check_failed,
                    timestamp=metric.timestamp
                )
                resource_data.utilization_status = get_utilization_status("EC2", {
                    "cpu_utilization": metric.cpu_utilization
                })
        
        elif service.name == "RDS":
            metric = db.query(RDSMetric).filter(
                RDSMetric.resource_id == resource.id
            ).order_by(RDSMetric.timestamp.desc()).first()
            if metric:
                resource_data.rds_metrics = RDSMetricResponse(
                    cpu_utilization=metric.cpu_utilization,
                    database_connections=metric.database_connections,
                    free_storage_space=metric.free_storage_space,
                    freeable_memory=metric.freeable_memory,
                    read_latency=metric.read_latency,
                    write_latency=metric.write_latency,
                    read_iops=metric.read_iops,
                    write_iops=metric.write_iops,
                    network_receive_throughput=metric.network_receive_throughput,
                    network_transmit_throughput=metric.network_transmit_throughput,
                    timestamp=metric.timestamp
                )
                resource_data.utilization_status = get_utilization_status("RDS", {
                    "cpu_utilization": metric.cpu_utilization,
                    "database_connections": metric.database_connections
                })
        
        elif service.name == "S3":
            metric = db.query(S3Metric).filter(
                S3Metric.resource_id == resource.id
            ).order_by(S3Metric.timestamp.desc()).first()
            if metric:
                resource_data.s3_metrics = S3MetricResponse(
                    bucket_size_bytes=metric.bucket_size_bytes,
                    number_of_objects=metric.number_of_objects,
                    all_requests=metric.all_requests,
                    get_requests=metric.get_requests,
                    put_requests=metric.put_requests,
                    delete_requests=metric.delete_requests,
                    bytes_downloaded=metric.bytes_downloaded,
                    bytes_uploaded=metric.bytes_uploaded,
                    first_byte_latency=metric.first_byte_latency,
                    errors_4xx=metric.errors_4xx,
                    errors_5xx=metric.errors_5xx,
                    timestamp=metric.timestamp
                )
                resource_data.utilization_status = get_utilization_status("S3", {
                    "all_requests": metric.all_requests
                })
        
        elif service.name == "Lambda":
            metric = db.query(LambdaMetric).filter(
                LambdaMetric.resource_id == resource.id
            ).order_by(LambdaMetric.timestamp.desc()).first()
            if metric:
                resource_data.lambda_metrics = LambdaMetricResponse(
                    invocations=metric.invocations,
                    duration_avg=metric.duration_avg,
                    duration_max=metric.duration_max,
                    errors=metric.errors,
                    throttles=metric.throttles,
                    concurrent_executions=metric.concurrent_executions,
                    dead_letter_errors=metric.dead_letter_errors,
                    iterator_age=metric.iterator_age,
                    provisioned_concurrency_invocations=metric.provisioned_concurrency_invocations,
                    timestamp=metric.timestamp
                )
                resource_data.utilization_status = get_utilization_status("Lambda", {
                    "invocations": metric.invocations,
                    "errors": metric.errors
                })
        
        resource_responses.append(resource_data)
    
    dept_breakdown = db.query(
        Department.name,
        func.sum(Resource.monthly_cost).label("total_cost")
    ).join(Resource, Resource.department_id == Department.id).filter(
        Resource.service_id == service.id
    ).group_by(Department.name).all()
    
    department_breakdown = [
        {"department": name, "cost": round(cost, 2)}
        for name, cost in dept_breakdown
    ]
    
    return ServiceDrilldown(
        service=ServiceResponse(
            id=service.id,
            name=service.name,
            service_type=service.service_type,
            monthly_cost=service.monthly_cost,
            category=service.category,
            percentage_of_total=round((service.monthly_cost / total_spend * 100), 1) if total_spend > 0 else 0,
            resource_count=len(resources)
        ),
        resources=resource_responses,
        total_cost=service.monthly_cost,
        department_breakdown=department_breakdown
    )

@router.get("/metrics/{resource_id}")
def get_resource_metrics(resource_id: int, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    service = db.query(Service).filter(Service.id == resource.service_id).first()
    
    metrics_data = {
        "resource_id": resource_id,
        "resource_name": resource.resource_name,
        "service_type": service.name if service else "Unknown",
        "metrics": None
    }
    
    if service.name == "EC2":
        metrics = db.query(EC2Metric).filter(
            EC2Metric.resource_id == resource_id
        ).order_by(EC2Metric.timestamp.desc()).limit(24).all()
        metrics_data["metrics"] = [
            {
                "cpu_utilization": m.cpu_utilization,
                "memory_utilization": m.memory_utilization,
                "network_in": m.network_in,
                "network_out": m.network_out,
                "disk_read_ops": m.disk_read_ops,
                "disk_write_ops": m.disk_write_ops,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    elif service.name == "RDS":
        metrics = db.query(RDSMetric).filter(
            RDSMetric.resource_id == resource_id
        ).order_by(RDSMetric.timestamp.desc()).limit(24).all()
        metrics_data["metrics"] = [
            {
                "cpu_utilization": m.cpu_utilization,
                "database_connections": m.database_connections,
                "free_storage_space": m.free_storage_space,
                "read_latency": m.read_latency,
                "write_latency": m.write_latency,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    elif service.name == "S3":
        metrics = db.query(S3Metric).filter(
            S3Metric.resource_id == resource_id
        ).order_by(S3Metric.timestamp.desc()).limit(24).all()
        metrics_data["metrics"] = [
            {
                "bucket_size_bytes": m.bucket_size_bytes,
                "number_of_objects": m.number_of_objects,
                "all_requests": m.all_requests,
                "get_requests": m.get_requests,
                "put_requests": m.put_requests,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    elif service.name == "Lambda":
        metrics = db.query(LambdaMetric).filter(
            LambdaMetric.resource_id == resource_id
        ).order_by(LambdaMetric.timestamp.desc()).limit(24).all()
        metrics_data["metrics"] = [
            {
                "invocations": m.invocations,
                "duration_avg": m.duration_avg,
                "errors": m.errors,
                "throttles": m.throttles,
                "concurrent_executions": m.concurrent_executions,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    
    return metrics_data
